--[[
  This file can be fed to shrinko8 via '--pico-script <this file>'
  Then, you can write:
  
    print("regular code")
    --$switch-compiler: parens8
    print("code transparently compiled into parens8")
    --$switch-compiler: none
    print("more regular code")

  The interpreter is automatically added before the first compilation,
  but you can also add it explicitly somewhere else via:
    --$dynamic-include: parens8.interpreter

  You can pass parens8 options to the compiler:
    --$switch-compiler: parens8 sparse_vararg rom=0x800
  All parens8 options are accepted, but the following are handled specially:
    rom=<addr> - compile to rom at the given address, instead of to a string
    rom_end=<addr> - finish compiling to rom at the given address.
                     if there is data left over, it will be compiled as a string
    vm_cleanup=<opt> - can be set to full or partial or none
]]

#include parens8_src/serializers/generic.lua
#include parens8_src/compilers/vmgen.lua
#include parens8_src/compilers/core.lua
#include parens8_src/compilers/platform/crescent_p8.lua
#include parens8_src/compilers/crescent.lua

local pico_process = python.import("pico_process")
local pico_output = python.import("pico_output")
local module = {}
local ROM_ENDADDR = 0x4300

Parens8Compiler = python.class(pico_process.CompilerBase)

function split_args(args_str)
    local args = {}
    for arg in all(split(args_str, ' ', false)) do
        arg = split(arg, '=')
        args[arg[1]] = arg[2] or true
    end
    return args
end

function copy(tbl)
    local copy = {}
    for k,v in pairs(tbl) do copy[k] = v end
    return copy
end
function tohex(v)
    return sub(tostr(v, 1), 1, 6)
end

function get_parens8_data(ctxt)
    return ctxt.get_field("parens8_data", function()
        return {num_compilers=0, results={}} -- has_interpreter=False, needs_reset=False
    end)
end

function reset(opts)
    -- called once done with cart (e.g. important in the webapp and in test runs)
    opidx, opcodes, vm_ops = unpack(get_parens8_data(opts.ctxt).reset_data)
    -- we don't copy here - they'll be copied in their initial state again next compilation
end

function Parens8Compiler:__init(opts)
    self.args = opts.args
    self.ctxt = opts.ctxt
    self.src = opts.src
    self.id = tostr(self, 1) -- used to identify this compiler instance inside strings

    get_parens8_data(self.ctxt).num_compilers += 1
end

function Parens8Compiler:get_dynamic_includes()
    local includes = {}
    if not get_parens8_data(self.ctxt).has_interpreter then
        add(includes, "parens8.interpreter " .. self.args)
        -- (guaranteed to set parens8.interpreter before next compilation)
    end
    add(includes, "parens8.run " .. self.id)
    return python.list(includes)
end

function Parens8Compiler:compile(root, opts)
    local code = pico_output.output_node(root, self.ctxt, --[[minify=]]false)
    local data = get_parens8_data(self.ctxt)

    -- save initial data to allow resetting it later
    if not data.needs_reset then
        data.reset_data = {opidx, copy(opcodes), copy(vm_ops)}
        python.attrs(self.ctxt.at_finish).append(reset)
        data.needs_reset = true
    end
    
    local cl_args = split_args(self.args)

    -- extract our options
    local rom_addr = cl_args.rom; cl_args.rom = nil
    if (rom_addr and type(rom_addr) != "number") rom_addr = 0
    local rom_endaddr = cl_args.rom_end; cl_args.rom_end = nil
    if (type(rom_endaddr) != "number" or rom_endaddr > ROM_ENDADDR) rom_endaddr = ROM_ENDADDR

    -- modify non-string options
    if not cl_args.vm_cleanup then
        cl_args.vm_cleanup = data.num_compilers == 1 and "full" or "partial"
    end
    cl_args.vm_cleanup = cl_args.vm_cleanup == "full" and vm_cleanup_full or
        cl_args.vm_cleanup != "none" and vm_cleanup_partial -- else empty
    
    if self.ctxt.global_renames then -- need to rename cleanups in tandem...
        cl_args.vm_cleanup = copy(cl_args.vm_cleanup)
        for i, cleanup in pairs(cl_args.vm_cleanup) do
            cl_args.vm_cleanup[i] = self.ctxt.global_renames[cleanup]
        end
    end

    local cl_code = compile_crescent(cl_args, code)
    local byte_code = shrinko.to_memory(serialize(cl_code))

    local results = data.results
    results[self.id] = ""

    if rom_addr then
        local max_len = min(rom_endaddr - rom_addr, #byte_code)
        local rom_data = byte_code.get_block(0, max_len)
        self.src.cart.rom.set_block(rom_addr, rom_data)
        results[self.id] ..= format("chr(peek(`1`, `2`))", {rom_addr, max_len})
        byte_code = byte_code.get_block(max_len, #byte_code - max_len)

        printh(format("parens8 - wrote `1` bytes to addresses `2` until `3` `4`",
            {max_len, tohex(rom_addr), tohex(rom_addr + max_len),
             #byte_code > 0 and format("(`1` bytes left)", {#byte_code}) or ""}))

        if (#byte_code == 0) return
        results[self.id] ..= ".."
    end

    results[self.id] ..= pico_output.format_string_literal(shrinko.from_memory(byte_code))
end

function get_parens8_interpreter(opts)
    local data = get_parens8_data(opts.ctxt)
    if data.has_interpreter then
        printh("error - interpreter already written out, can't write it again") -- or could we?
    else
        data.has_interpreter = true

        local template = string.gsub(vm_template, '"`compiled_args`"', '--[[$placeholder-expr::parens8.interp_args]] ""')
        template = string.gsub(template, 'return `runtime_ops`', '--[[$placeholder-stmt::parens8.interp_ops]] do end')
        -- 'preserve' locals used by vm ops. ideally we'd (or shrinko'd) rename the vm ops instead but it's not trivial at all...
        template = string.gsub(template, 'ps8_runtime%(a, b, c%)', 'ps8_runtime(--[[$rename::a]]a, --[[$rename::b]]b, --[[$rename::c]]c)')
        return fp_boilerplate .. deserializer .. template
    end
end

function get_parens8_interp_ops(opts)
    local opfuncs = {}
    for opcode, vm_op in ipairs(vm_ops) do
		opfuncs[opcode] = vm_op[2]
	end
	return "return " .. join(opfuncs, ",\n")
end

function get_parens8_interp_args(opts)
    local compiled_args = {}
    for opcode, vm_op in ipairs(vm_ops) do
		compiled_args[opcode] = vm_op[1]
	end
	return '"' .. join(compiled_args, ",") .. '"'
end

function get_parens8_run_code(opts)
    return format('run_ps8(deserialize(--[[$placeholder-expr::parens8.result `1`]] ""))', {opts.args})
end

function get_parens8_result(opts)
    return get_parens8_data(opts.ctxt).results[opts.args]
end

function module.include_main(name)
    if (name == "parens8.interpreter") return get_parens8_interpreter
    if (name == "parens8.interp_ops") return get_parens8_interp_ops
    if (name == "parens8.interp_args") return get_parens8_interp_args
    if (name == "parens8.run") return get_parens8_run_code
    if (name == "parens8.result") return get_parens8_result
end

function module.compiler_main(name)
    if (name == "parens8") return Parens8Compiler
end

return module
