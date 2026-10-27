"""Definition of the pico8 context (builtins, etc) and functions to do all our processing (delegating to individual modules)"""

from utils import *
from pico_defs import Language, from_langstr
from pico_compress import print_size
from pico_srcdefs import *
from pico_tokenize import tokenize, count_tokens
from pico_parse import parse, create_super_root, get_sub_root
from pico_lint import lint_code
from pico_minify import minify_code
from pico_unminify import unminify_code
from pico_constfold import fold_consts
from pico_output import output_code, output_needs_comments
from pico_rename import rename_tokens

# re-export some things for old examples to keep working.
from pico_tokenize import is_identifier, is_ident_char, TokenType
from pico_parse import Local, Global, Scope

# when adding new builtins:
#   check whether to update builtins_copied_to_locals (find 'local ...=...' script inside pico8 binary; e.g. `strings $(which pico8) | grep "^local "`)
#   consider whether to update builtins_with_callbacks

builtin_globals = {
    # normal
    "abs", "add", "all", "assert", "atan2", "btn", "btnp",
    "camera", "cartdata", "ceil", "chr", "circ", "circfill",
    "clip", "cls", "cocreate", "color", "coresume", "cos",
    "costatus", "count", "cstore", "cursor", "del", "deli",
    "dget", "dset", "extcmd", "fget", "fillp", "flip",
    "flr", "foreach", "fset", "getmetatable", "ipairs", "inext",
    "line", "load", "ls", "map", "max", "memcpy", "memset",
    "menuitem", "mget", "mid", "min", "mset", "music",
    "next", "ord", "oval", "ovalfill", "pack", "pairs",
    "pal", "palt", "peek", "peek2", "peek4", "pget",
    "poke", "poke2", "poke4", "print", "printh", "pset",
    "rawequal", "rawget", "rawlen", "rawset", "rect",
    "rectfill", "reload", "reset", "rnd", "rrect", "rrectfill",
    "run", "select", "setmetatable",
    "serial", "sfx", "sget", "sgn", "sin", "split",
    "spr", "sqrt", "srand", "sset", "sspr", "stat", "stop",
    "sub", "time", "tline", "tonum", "tostr", "trace", "type",
    "unpack", "yield", "t",
    # deprecated
    "band", "bnot", "bor", "bxor",
    "lshr", "rotl", "rotr", "shl", "shr",
    "mapdraw", 
    # undocumented
    "holdframe", "_set_fps", "_update_buttons", "_mark_cpu",
    "_startframe", "_update_framerate", "_set_mainloop_exists",
    "_map_display", "_get_menu_item_selected", "_pausemenu",
    "set_draw_slice", "tostring",
}

# pattern builtins
builtin_globals |= set(chr(ch) for ch in range(0x80, 0x9a))

# subset of builtins that pico8 copies to top-level locals
# (builtins included here must also be in builtin_globals)
builtins_copied_to_locals = {
    "time", "sub", "chr", "ord", "tostr", "tonum", "add",
    "del", "deli", "clip", "color", "pal", "palt", "fillp",
    "pget", "pset", "sget", "sset", "fget", "fset",
    "circ", "circfill", "rect", "rectfill", "oval", "ovalfill",
    "line", "spr", "sspr",
    "mget", "mset", "tline", "peek", "poke", "peek2", "poke2",
    "peek4", "poke4", "memcpy", "memset", "max", "min", "mid",
    "flr", "ceil", "cos", "sin", "atan2", "srand", "band", # note: rnd is missing due to a pico8 typo
    "bor", "bxor", "bnot", "shl", "shr", "lshr", "rotl", "rotr",
}

# subset of builtins that may call user code before returning, NOT including far-fetched stuff like metamethods
# (builtins included here must also be in builtin_globals)
builtins_with_callbacks = {
    "coresume", "foreach", "yield",
}

# callbacks that are called by the builtin mainloop logic
builtin_callbacks = {
    "_init", "_draw", "_update", "_update60",
}

# table members that are used by builtins
builtin_members = {
    # pack()
    "n",
    # metamethods:
    "__index", "__newindex", "__len", "__eq", "__lt", "__le",
    "__add", "__sub", "__mul", "__div", "__idiv", "__mod",
    "__pow", "__and", "__or", "__xor", "__shl", "__shr",
    "__lshr", "__rotl", "__rotr", "__concat", "__unm", "__not",
    "__peek", "__peek2", "__peek4", "__call", "__tostring",
    "__pairs", "__ipairs", "__metatable", "__gc", "__mode",
}

class PicoContext(ContextBase):
    """Specialization of ContextBase to pico8 - specifying its builtins, etc."""
    def __init__(m, **opts):
        super().__init__(Language.pico8, builtin_globals, builtins_copied_to_locals, builtins_with_callbacks, builtin_callbacks, builtin_members, **opts)

def print_token_count(num_tokens, **kwargs):
    print_size("tokens", num_tokens, 8192, **kwargs)

def fixup_process_args(args):
    if args is True:
        args = {}
    args_set = isinstance(args, dict)
    return args_set, args

def process_compiler(token):
    token.compiler.compile(token.compiler_root)
    token.compiler_node.erase(keep_comments=False)
    # compiler outputs are processed via placeholders

def process_placeholder(ctxt, token, errors):
    ph_name, ph_args = token.placeholder_name, token.placeholder_args
    include_func = ctxt.include_getter(ph_name, placeholder=True)
    if include_func:
        ph_str = include_func(args=ph_args.strip(), ctxt=ctxt)
        if ph_str != None:
            ph_source = Source(ph_name, ph_str)
            ph_tokens, ph_errors = tokenize(ph_source, ctxt, inner=True)
            if not ph_errors:
                ph_root, ph_errors = parse(ph_source, ph_tokens, ctxt, for_expr=token.placeholder_expr)
                if not ph_errors:
                    token.parent.replace_with(ph_root)
                    return
            errors += ph_errors
    
    eprint(f"placeholder '{ph_name}' is not recognized")

def process_code(ctxt, source, input_count=False, count=False, lint=False, minify=False, rename=False, unminify=False, 
                 stop_on_lint=True, count_is_optional=False, preproc=None):
    """Do everything (minify, lint, etc) to the code that was requested - including parsing/tokenizing it if/as needed"""

    need_lint, lint = fixup_process_args(lint)
    need_minify, minify = fixup_process_args(minify)
    need_rename, rename = fixup_process_args(rename)
    need_unminify, unminify = fixup_process_args(unminify)

    if not need_lint and not need_minify and not need_unminify and not ((count or input_count) and not count_is_optional) and not preproc:
        return True, ()
    
    need_parse = need_lint or need_minify or need_unminify or preproc
    need_all_comments = need_unminify or (need_minify and output_needs_comments(minify))

    errors = ()
    root = create_super_root() if source.is_super else None
    subsrc_count = 0
    for subsrc in source:
        subsrc_count += 1
        tokens, errors = tokenize(subsrc, ctxt, need_all_comments)
        if not errors and need_parse:
            root, errors = parse(subsrc, tokens, ctxt, root)
        if errors:
            return False, errors

    if subsrc_count:
        if source.is_super:
            source.sort_root(root)

        if input_count:
            assert not source.is_super
            print_token_count(count_tokens(tokens), prefix="input", handler=input_count)

        if need_lint:
            errors = lint_code(ctxt, root, lint)

        if preproc: # can do linting and early transformations
            def add_error(msg, node):
                errors.append(Error(msg, node))
            preproc(root, add_error)
        
        if not errors or not stop_on_lint:        
            if need_minify:
                simplify_code(ctxt, root, minify, errors)
                
                if need_rename:
                    rename_tokens(ctxt, root, rename)
                
                transform_code(ctxt, root, minify, errors)

                minify_code(ctxt, root, minify)

                for subsrc in source:
                    subsrc.text = output_code(ctxt, get_sub_root(root, subsrc), minify)
            
            if need_unminify:
                for subsrc in source:
                    subsrc.text = unminify_code(get_sub_root(root, subsrc), unminify)

            if count:
                assert not source.is_super
                new_tokens = root.get_tokens() if need_parse else tokens
                print_token_count(count_tokens(new_tokens), handler=count)

    return True, errors

def simplify_code(ctxt, root, minify, errors):
    fold = minify.get("consts", True)
        
    if fold:
        fold_consts(ctxt, minify, root, errors)

def transform_code(ctxt, root, minify, errors):
    transform = minify.get("transform", True)
        
    if transform:
        for compiler_token in root.compiler_tokens:
            process_compiler(compiler_token)
        
        for placeholder_token in root.placeholders:
            process_placeholder(ctxt, placeholder_token, errors)

def echo_code(code, ctxt, echo=True):
    code = from_langstr(code, ctxt.lang)
    if echo == True:
        for line in code.splitlines():
            print(line)
    else:
        file_write_maybe_text(echo, code)    
