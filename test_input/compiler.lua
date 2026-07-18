local CompilerBase = python.import("pico_process").CompilerBase
local module = {}

ReplCompiler = python.class(CompilerBase)

-- we store a table on the ctxt with all the code
function ctxt_get_repl_code_table(ctxt)
    return ctxt.get_field("repl_code", function() return {} end)
end

-- A sample compiler that actually just inserts the compiled code
-- as a string argument to a p8 function
-- (E.g. could've been used for the repl at https://www.lexaloffle.com/bbs/?tid=36381)
function ReplCompiler:__init(opts)
    self.args = {}
    for arg in all(split(opts.args, ' ')) do
        self.args[arg] = true
    end

    self.ctxt = opts.ctxt
    self.src = opts.src
    self.id = tostr(self, 1) -- used to identify this compiler instance inside strings
end

-- should return any names of dynamic includes that should be inserted in the code
-- immediately after the --$switch-compiler: (resolved via include_main)
-- for simple cases, that's just the code that runs the underlying interpreter (+ placeholder for the compiled code)
-- for complex cases, you can also include the interpreter itself - unless previously included elsewhere
--   via an explicit --$dynamic-include: (can check via flag on ctxt)
-- and you can have placeholders in the interpreter too - allowing to add more ops to the interpreter
--   depending on what ops are used in the compiled code
function ReplCompiler:get_dynamic_includes()
    local includes = {"repl.include " .. self.id}
    return python.list(includes)
end

-- receives a syntax tree root node
-- should compile it and store the results for later use by the placeholder(s)
function ReplCompiler:compile(root)
    -- for p8 scripts, we currently have only one viable option -
    -- convert the syntax tree into code and reparse it via some p8 code
    -- (note - it's faster to convert to code without minifying)
    
    -- here, we convert it into optionally minified code
    local output_node = python.import("pico_output").output_node
    local minify = self.args["+minify"]
    local code = output_node(root, self.ctxt, minify)

    local repl_code_map = ctxt_get_repl_code_table(self.ctxt)
    if self.args["+rom"] then
        -- a special mode in which the code will be encoded into rom
        -- (would probably want to supply the address via self.args too)
        self.src.cart.rom.set_block(0, shrinko.to_memory(code))
        repl_code_map[self.id] = "chr(peek(0, "..#code.."))"
    else
        -- the regular mode in which the code is inserted in a string
        local format_string_literal = python.import("pico_output").format_string_literal
        repl_code_map[self.id] = format_string_literal(code)
    end
end

-- this is called by request of ReplCompiler.get_dynamic_include
function get_repl_include(opts)
    -- since this is an include, the returned code can freely access globals/etc
    return 'execute_raw(--[[$placeholder::repl.code '..opts.args..']]"", _ENV)'
end

-- this is called by request of above --[[$placeholder::...]], after rename but before minify
function get_repl_code(opts)
    -- since this is a placeholder, the returned code must not access any variables that might've been renamed
    -- (it can still access _ENVs and builtins)
    local repl_code_map = ctxt_get_repl_code_table(opts.ctxt)
    return repl_code_map[opts.args] -- in our case, args is the compiler's id we passed through the include and the placeholder
end

-- this is called to get any includes & placeholders for the compiler
function module.include_main(name)
    if (name == "repl.include") return get_repl_include
    if (name == "repl.code") return get_repl_code
    if (name == "repl.dummy") return function () return "print(execute_raw(123, nil))" end -- do not copy to README...
end

-- this is called to get a compiler class by name
function module.compiler_main(name)
    if (name == "repl") return ReplCompiler
end

return module