from utils import *
from pico_defs import Language, from_langstr
from pico_compress import print_size
from pico_preprocess import k_tab_break

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
    
    # not a super-source
    is_super = False
    def __iter__(m):
        yield m

class CartSource(Source):
    """The source of a pico8 cart, maps indexes in the preprocessed code to individual source files"""
    def __init__(m, cart, _=None):
        m.cart = cart
        m.mappings = cart.code_map
        # no super().__init__ - we override with properties

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
    def get_used_globals(m, **_):
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

class ContextBase:
    """Defines information for how code is to be processed, e.g. the supported builtins, the supported version, the language, etc."""
    def __init__(m, lang, builtins, local_builtins, builtins_with_callbacks, builtin_callbacks, builtin_members,
                 extra_builtins=None, not_builtins=None, use_local_builtins=True, extra_local_builtins=None, 
                 srcmap=False, sublang_getter=None, version=sys.maxsize, hint_comments=True, consts=None):
        m.builtins = builtins.copy()
        m.local_builtins = local_builtins.copy() if use_local_builtins else set()
        m.builtins_with_callbacks = builtins_with_callbacks
        m.builtin_callbacks = builtin_callbacks
        m.builtin_members = builtin_members
        
        if extra_builtins:
            m.builtins |= set(extra_builtins)
        if not_builtins:
            m.builtins -= set(not_builtins)
            m.local_builtins -= set(not_builtins)
        if extra_local_builtins:
            m.builtins |= set(extra_local_builtins)
            m.local_builtins |= set(extra_local_builtins)

        m.srcmap = [] if srcmap else None
        m.consts = consts
        m.sublang_getter = sublang_getter
        m.custom_langdefs = None
        m.hint_comments = hint_comments
        m.version = version
        m.lang = lang
    
    def add_custom_langdef(m, source, target, args):
        if m.custom_langdefs is None:
            m.custom_langdefs = {}
        m.custom_langdefs[source] = (target, args)
    
    def map_langdef(m, name, args):
        while m.custom_langdefs and name in m.custom_langdefs:
            name, pre_args = m.custom_langdefs[name]
            if pre_args:
                if args:
                    args = pre_args + " " + args
                else:
                    args = pre_args
        return name, args

class PicoContext(ContextBase):
    """Specialization of ContextBase to pico8"""
    def __init__(m, **opts):
        super().__init__(Language.pico8, builtin_globals, builtins_copied_to_locals, builtins_with_callbacks, builtin_callbacks, builtin_members, **opts)

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
        path = path_absolute(loc.path) if fmt == ErrorFormat.absolute else path_relative(loc.path)
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
                 stop_on_lint=True, count_is_optional=False, preproc=None):
    need_lint, lint = fixup_process_args(lint)
    need_minify, minify = fixup_process_args(minify)
    need_rename, rename = fixup_process_args(rename)
    need_unminify, unminify = fixup_process_args(unminify)

    if not need_lint and not need_minify and not need_unminify and not ((count or input_count) and not count_is_optional) and not preproc:
        return True, ()
    
    need_parse = need_lint or need_minify or need_unminify or preproc
    need_all_comments = need_unminify or (need_minify and minify_needs_comments(minify))

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

        if preproc: # can do linting and - theoretically - early transformations
            def add_error(msg, node):
                errors.append(Error(msg, node))
            preproc(root, add_error)
        
        if not errors or not stop_on_lint:        
            if need_minify:
                simplify_code(ctxt, root, minify, errors)
                
                if need_rename:
                    rename_tokens(ctxt, root, rename)

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

def echo_code(code, ctxt, echo=True):
    code = from_langstr(code, ctxt.lang)
    if echo == True:
        for line in code.splitlines():
            print(line)
    else:
        file_write_maybe_text(echo, code)    

from pico_tokenize import tokenize, count_tokens
from pico_parse import parse, create_super_root, get_sub_root
from pico_lint import lint_code
from pico_minify import minify_code, minify_needs_comments, Focus
from pico_unminify import unminify_code
from pico_constfold import fold_consts
from pico_output import output_code
from pico_rename import rename_tokens

# re-export some things for examples/etc.
from pico_tokenize import is_identifier, is_ident_char
from pico_parse import Local, Global, Scope
