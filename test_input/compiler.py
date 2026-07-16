from pico_process import CompilerBase

def ctxt_get_repl_code_map(ctxt): # we store the code on the ctxt, using a sufficiently unique name to avoid conflicts
    return ctxt.__dict__.setdefault("_repl_code", {})

class ReplCompiler(CompilerBase):
    # A sample compiler that actually just inserts the compiled code
    # as a string argument to a p8 function
    # (E.g. could've been used for the repl at https://www.lexaloffle.com/bbs/?tid=36381)
    def __init__(self, ctxt, src, args, **_):
        self.ctxt = ctxt
        self.args = args.split()
        self.src = src
        self.id = str(id(self)) # used to identify this compiler instance inside strings

    # should return any names of dynamic includes that should be inserted in the code
    # immediately after the --switch-compiler: (resolved via include_main)
    # for simple cases, that's just the code that runs the underlying interpreter (+ placeholder for the compiled code)
    # for complex cases, you can also include the interpreter itself - unless previously included elsewhere
    #   via an explicit --dynamic-include: (can check via flag on ctxt)
    # and you can have placeholders in the interpreter too - allowing to add more ops to the interpreter
    #   depending on what ops are used in the compiled code
    def get_dynamic_includes(self, **_):
        return ["repl.include " + self.id]
    
    # receives a syntax tree root node
    # should compile it and store the results for later use by the placeholder(s)
    def compile(self, root, **_):
        # we have two options - compile the already parsed syntax tree 
        #   (see preprocess_syntax_main in the README for how this could be done)
        # or convert it into code and reparse it via some external library, if preferred.
        #   (note - it's faster to convert to code without minifying)
        
        # here, we convert it into optionally minified code
        from pico_output import output_node
        code = output_node(root, self.ctxt, minify="+minify" in self.args)

        repl_code_map = ctxt_get_repl_code_map(self.ctxt)
        if "+rom" in self.args:
            # a special mode in which the code will be encoded into rom
            # (would probably want to supply the address via self.args too)
            from pico_defs import encode_p8str
            enc_code = encode_p8str(code)
            enc_len = len(enc_code)
            self.src.cart.rom[:enc_len] = enc_code
            repl_code_map[self.id] = f"chr(peek(0, {enc_len}))"
        else:
            # the regular mode in which the code is inserted in a string
            from pico_output import format_string_literal
            repl_code_map[self.id] = format_string_literal(code)

# this is called by request of ReplCompiler.get_dynamic_include
def get_repl_include(args, **_):
    # since this is an include, the returned code can freely access globals/etc
    return f'execute_raw(--[[placeholder::repl.code {args}]]"", _ENV)'

# this is called by request of above --[[placeholder::...]], after rename but before minify
def get_repl_code(args, ctxt, **_):
    # since this is a placeholder, the returned code must not access any variables that might've been renamed
    # (it can still access _ENVs and builtins)
    repl_code_map = ctxt_get_repl_code_map(ctxt)
    return repl_code_map.get(args) # in our case, args is the compiler's id we passed through the include and the placeholder

# this is called to get any includes & placeholders for the compiler
def include_main(name, **_):
    if name == "repl.include":
        return get_repl_include
    elif name == "repl.code":
        return get_repl_code
    elif name == "repl.dummy": # do not copy to README...
        return lambda **_: "print(execute_raw(123, nil))"

# this is called to get a compiler class by name
def compiler_main(name, **_):
    if name == "repl":
        return ReplCompiler
