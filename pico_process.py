from utils import *
from pico_defs import from_pico_chars
from pico_cart import print_size

main_globals = {
    "abs", "add", "all", "assert", "atan2", "btn", "btnp",
    "camera", "cartdata", "ceil", "chr", "circ", "circfill",
    "clip", "cls", "cocreate", "color", "coresume", "cos",
    "costatus", "count", "cstore", "cursor", "del", "deli",
    "dget", "dset", "extcmd", "fget", "fillp", "flip",
    "flr", "foreach", "fset", "getmetatable", "ipairs", "inext",
    "line", "load", "map", "max", "memcpy", "memset",
    "menuitem", "mget", "mid", "min", "mset", "music",
    "next", "ord", "oval", "ovalfill", "pack", "pairs",
    "pal", "palt", "peek", "peek2", "peek4", "pget",
    "poke", "poke2", "poke4", "print", "printh", "pset",
    "rawequal", "rawget", "rawlen", "rawset", "rect",
    "rectfill", "reload", "rnd", "run", "select", "setmetatable",
    "serial", "sfx", "sget", "sgn", "sin", "split",
    "spr", "sqrt", "srand", "sset", "sspr", "stat", "stop",
    "sub", "time", "tline", "tonum", "tostr", "trace", "type",
    "unpack", "yield", "t",
}

deprecated_globals = {
    "band", "bnot", "bor", "bxor",
    "lshr", "rotl", "rotr", "shl", "shr",
    "mapdraw", 
}

undocumented_globals = {
    "holdframe", "_set_fps", "_update_buttons",
    "_map_display", "_get_menu_item_selected",
    "set_draw_slice",
}

pattern_globals = set(chr(ch) for ch in range(0x80, 0x9a))

def get_line_col(text, idx): # (0-based)
    start = 0
    line = 0

    while start < idx:
        end = text.find("\n", start)
        if end < 0 or end >= idx:
            break
        line += 1
        start = end + 1
    
    return line, idx - start

class PicoSource: # keep this light - created for temp. tokenizations
    __slots__ = ("name", "text")

    def __init__(m, name, text):
        m.name, m.text = name, text
        
    def get_name_line_col(m, idx): # (0-based)
        line, col = get_line_col(m.text, idx)        
        return m.name, line, col

class CartSource(PicoSource):
    def __init__(m, cart):
        m.cart = cart
        m.mappings = cart.code_map
        # no __init__ - we override with properties

    def get_name_line_col(m, idx):
        for mapping in reversed(m.mappings):
            if idx >= mapping.idx:
                name = mapping.src_name
                line, col = get_line_col(mapping.src_code, mapping.src_idx + (idx - mapping.idx))
                return name, line + mapping.src_line, col
        
        return super().get_name_line_col(idx)

    @property
    def name(m):
        return m.cart.name
        
    @property
    def text(m):
        return m.cart.code

    @text.setter
    def text(m, val):
        m.cart.set_code(val)

class SubLanguageBase:
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
    def __init__(m, deprecated=True, undocumented=True, patterns=True, srcmap=False, extra_globals=None, sublang_getter=None):
        funcs = set(main_globals)
        if deprecated:
            funcs |= deprecated_globals
        if undocumented:
            funcs |= undocumented_globals
        if patterns:
            funcs |= pattern_globals
        if extra_globals:
            funcs |= set(extra_globals)

        m.globals = funcs

        m.srcmap = [] if srcmap else None
        m.sublang_getter = sublang_getter

class Error:
    def __init__(m, msg, token):
        m.msg, m.token = msg, token

    def __str__(m):
        token = m.token
        name, line, col = token.source.get_name_line_col(token.idx) if token.source else ("???", 0, 0)
        return "%s(%s:%s) - %s" % (name, line + 1, col + 1, m.msg)

def print_token_count(num_tokens, **kwargs):
    print_size("tokens", num_tokens, 8192, **kwargs)

def process_code(ctxt, source, input_count=False, count=False, lint=False, minify=False, rename=False, fail=True):
    need_lint = lint not in (None, False)
    need_minify = minify not in (None, False)
    need_rename = rename not in (None, False)

    ok = False
    tokens, errors = tokenize(source, ctxt)
    if not errors and (need_lint or need_minify):
        root, errors = parse(source, tokens)
        
    if not errors:
        ok = True

        if input_count:
            print_token_count(count_tokens(tokens), prefix="input", handler=input_count)

        if need_lint:
            errors = lint_code(ctxt, tokens, root, lint)
        
        if need_minify:
            if need_rename:
                rename_tokens(ctxt, root, rename)

            source.text, tokens = minify_code(source, tokens, root, minify)

        if count:
            print_token_count(count_tokens(tokens), handler=count)

    if fail and errors:
        raise Exception("\n".join(map(str, errors)))
    return ok, errors

def echo_code(code, echo=True):
    code = from_pico_chars(code)
    if echo == True:
        for line in code.splitlines():
            print(line)
    else:
        file_write_text(echo, code)    

from pico_tokenize import tokenize, count_tokens
from pico_parse import parse
from pico_lint import lint_code
from pico_minify import minify_code
from pico_rename import rename_tokens

# re-export some things for examples/etc.
from pico_tokenize import is_identifier, is_ident_char, CustomPreprocessor
from pico_parse import Local, Global, Scope
