from utils import *
from pico_defs import from_p8str
from pico_compress import print_size
from pico_preprocess import k_tab_break

# when adding new globals:
#   check whether to update builtins_copied_to_locals (find 'local ...=...' script inside pico8 binary; e.g. `strings $(which pico8) | grep "^local "`)
#   consider whether to update builtins_with_callbacks

main_builtins = {
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
    "rectfill", "reload", "reset", "rnd", "run", "select", "setmetatable",
    "serial", "sfx", "sget", "sgn", "sin", "split",
    "spr", "sqrt", "srand", "sset", "sspr", "stat", "stop",
    "sub", "time", "tline", "tonum", "tostr", "trace", "type",
    "unpack", "yield", "t",
}

deprecated_builtins = {
    "band", "bnot", "bor", "bxor",
    "lshr", "rotl", "rotr", "shl", "shr",
    "mapdraw", 
}

undocumented_builtins = {
    "holdframe", "_set_fps", "_update_buttons", "_mark_cpu",
    "_startframe", "_update_framerate", "_set_mainloop_exists",
    "_map_display", "_get_menu_item_selected", "_pausemenu",
    "set_draw_slice", "tostring",
}

pattern_builtins = set(chr(ch) for ch in range(0x80, 0x9a))

builtins_copied_to_locals = { # builtins listed here should also be listed elsewhere above!
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

builtins_with_callbacks = { # builtins listed here may call user code before returning, NOT including far-fetched stuff like metamethods
    "coresume", "foreach", "yield",
}

def get_line_col(text, idx, start=0): # (0-based)
    line = 0

    while start < idx:
        end = text.find("\n", start)
        if end < 0 or end >= idx:
            break
        line += 1
        start = end + 1
    
    return line, idx - start

def get_tab_line_col(text, idx, start=0): # (0-based)
    tab = 0

    while start < idx and tab < 15:
        end = text.find(k_tab_break, start)
        if end < 0 or end >= idx:
            break
        tab += 1
        start = end + len(k_tab_break)
    
    line, col = get_line_col(text, idx, start)
    return tab, line, col

class SourceLocation(Tuple):
    """A location in a source file (optionally with a tab)"""
    path = tab = line = col = ... # (0-based)

def get_source_location(path, text, idx, start_line=0, tabs=False):
    if tabs:
        tab, line, col = get_tab_line_col(text, idx)
    else:
        tab, line, col = None, *get_line_col(text, idx)
    return SourceLocation(path, tab, line + start_line, col)

class Source: # keep this light - created for temp. tokenizations
    """A pico8 source file - e.g. either the main one or an included file"""
    path = text = ...

    def __init__(m, path, text):
        m.path, m.text = path, text
        
    def get_location(m, idx, tabs=False): # (0-based)
        return get_source_location(m.path, m.text, idx, tabs=tabs)

class CartSource(Source):
    """The source of a pico8 cart, maps indexes in the preprocessed code to individual source files"""
    def __init__(m, cart):
        m.cart = cart
        m.mappings = cart.code_map
        # no __init__ - we override with properties

    def get_location(m, idx, tabs=False):
        for mapping in reversed(m.mappings):
            if idx >= mapping.idx:
                mapped_idx = mapping.src_idx + (idx - mapping.idx)
                return get_source_location(mapping.src_path, mapping.src_code, mapped_idx, mapping.src_line, tabs=tabs)
        
        return super().get_location(idx, tabs)

    @property
    def path(m):
        return m.cart.path
        
    @property
    def text(m):
        return m.cart.code

    @text.setter
    def text(m, val):
        m.cart.set_code_without_title(val)

class SubLanguageBase:
    """Base class of a custom 'sub-language' (a language embedded in a pico8 string, see README for more info),
    defining how to minify/lint/etc itself"""
    def __init__(m, str, **_):
        pass
    def get_defined_globals(m, **_):
        return () 
    def lint(m, **_):
        pass
    get_unminified_chars = None
    def get_global_usages(m, **_):
        return dict()
    def get_member_usages(m, **_):
        return dict()
    def get_local_usages(m, **_):
        return dict()
    def rename(m, **_):
        pass
    minify = None

class PicoContext:
    """Defines information for how pico8 code is to be processed, e.g. the supported builtins and the supported pico8 version"""
    def __init__(m, deprecated=True, undocumented=True, patterns=True, srcmap=False, extra_builtins=None, not_builtins=None, 
                 local_builtins=True, extra_local_builtins=None, sublang_getter=None, version=sys.maxsize, hint_comments=True,
                 consts=None):
        builtins = set(main_builtins)
        local_builtins = set(builtins_copied_to_locals) if local_builtins else set()
        if deprecated:
            builtins |= deprecated_builtins
        if undocumented:
            builtins |= undocumented_builtins
        if patterns:
            builtins |= pattern_builtins
        if extra_builtins:
            builtins |= set(extra_builtins)
        if not_builtins:
            builtins -= set(not_builtins)
            local_builtins -= set(not_builtins)
        if extra_local_builtins:
            builtins |= set(extra_local_builtins)
            local_builtins |= set(extra_local_builtins)

        m.builtins = builtins
        m.local_builtins = local_builtins
        m.callback_builtins = builtins_with_callbacks

        m.srcmap = [] if srcmap else None
        m.consts = consts
        m.sublang_getter = sublang_getter
        m.hint_comments = hint_comments
        m.version = version

class ErrorFormat(Enum):
    common = absolute = tabbed = ...

class Error:
    """An error (or warning) to be reported together with where in the source it occured"""
    def __init__(m, msg, token):
        m.msg, m.token = msg, token

    def __lt__(m, other):
        return m.token.idx < other.token.idx

    def format(m, fmt=None):
        fmt = default(fmt, ErrorFormat.common)
        tabbed = fmt == ErrorFormat.tabbed
        token = m.token
        loc = token.source.get_location(token.idx, tabs=tabbed) if token.source else SourceLocation("???", 0, 0, 0)
        path = path_absolute(loc.path) if fmt == ErrorFormat.absolute else path_relative(loc.path, fallback=True)
        if tabbed:
            return f"{path} (tab {loc.tab:X}, line {loc.line + 1}, col {loc.col + 1}): {m.msg}"
        else:
            return f"{path}:{loc.line + 1}:{loc.col + 1}: {m.msg}"

    def __str__(m):
        return m.format()

def print_token_count(num_tokens, **kwargs):
    print_size("tokens", num_tokens, 8192, **kwargs)

def fixup_process_args(args):
    if args is True:
        args = {}
    args_set = isinstance(args, dict)
    return args_set, args

def process_code(ctxt, source, input_count=False, count=False, lint=False, minify=False, rename=False, unminify=False, 
                 stop_on_lint=True, want_count=True):
    need_lint, lint = fixup_process_args(lint)
    need_minify, minify = fixup_process_args(minify)
    need_rename, rename = fixup_process_args(rename)
    need_unminify, unminify = fixup_process_args(unminify)

    if not need_lint and not need_minify and not need_unminify and not (want_count and (count or input_count)):
        return True, ()
    
    need_parse = need_lint or need_minify or need_unminify
    need_all_comments = need_unminify or (need_minify and minify_needs_comments(minify))

    ok = False
    tokens, errors = tokenize(source, ctxt, need_all_comments)
    if not errors and need_parse:
        root, errors = parse(source, tokens, ctxt)
    
    new_text = None
    if not errors:
        ok = True

        if input_count:
            print_token_count(count_tokens(tokens), prefix="input", handler=input_count)

        if need_lint:
            errors = lint_code(ctxt, root, lint)
        
        if not errors or not stop_on_lint:        
            if need_minify:
                simplify_code(ctxt, root, minify, errors)
                
                if need_rename:
                    rename_tokens(ctxt, root, rename)

                new_text = minify_code(ctxt, root, minify)
            
            if need_unminify:
                new_text = unminify_code(root, unminify)

            if count:
                new_tokens = root.get_tokens() if need_parse else tokens
                print_token_count(count_tokens(new_tokens), handler=count)

    if e(new_text):
        source.text = new_text

    return ok, errors

def simplify_code(ctxt, root, minify, errors):
    fold = minify.get("consts", True)
        
    if fold:
        fold_consts(ctxt, root, errors)

def echo_code(code, echo=True):
    code = from_p8str(code)
    if echo == True:
        for line in code.splitlines():
            print(line)
    else:
        file_write_text(echo, code)    

from pico_tokenize import tokenize, count_tokens
from pico_parse import parse
from pico_lint import lint_code
from pico_minify import minify_code, minify_needs_comments
from pico_unminify import unminify_code
from pico_constfold import fold_consts
from pico_rename import rename_tokens

# re-export some things for examples/etc.
from pico_tokenize import is_identifier, is_ident_char
from pico_parse import Local, Global, Scope
from pico_preprocess import CustomPreprocessor
