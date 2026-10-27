"""Basic definitions relating to source code, context, errors, etc."""

from utils import *
from pico_preprocess import k_tab_break

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
    """Base class of a custom 'sub-language' instance (a language embedded in a pico8 string, see README for more info),
    defining how to minify/lint/etc itself.
    See readme for documentation & description of members."""
    def __init__(m, str, **_):
        pass
    def get_defined_globals(m, **_):
        return ()
    def get_used_globals(m, **_):
        return ()
    def lint(m, **_):
        pass
    get_unminified_chars = None # or def get_unminified_chars(m, **_):
    def get_global_usages(m, **_):
        return dict()
    def get_member_usages(m, **_):
        return dict()
    def get_local_usages(m, **_):
        return dict()
    def rename(m, **_):
        pass
    minify = None # or def minify(m, **_):

class CompilerBase:
    """Base class of a custom compiler instance (which can process pico8 code between rename and minify)
    See readme for documentation & description of members."""
    def __init__(m, **_):
        pass
    def get_dynamic_includes(m, **_):
        return ()
    def compile(m, root, **_):
        pass

@context_manager("finish")
class ContextBase:
    """Defines information for how code is to be processed, e.g. the supported builtins, the supported version, the language, etc."""
    def __init__(m, lang, builtins, local_builtins, builtins_with_callbacks, builtin_callbacks, builtin_members,
                 extra_builtins=None, not_builtins=None, use_local_builtins=True, extra_local_builtins=None, 
                 srcmap=False, include_getter=None, sublang_getter=None, compiler_getter=None, default_compiler=None,
                 version=sys.maxsize, hint_comments=True, consts=None, ignore_transforms=False):
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
        m.ignore_transforms = ignore_transforms
        m.include_getter = include_getter
        m.sublang_getter = sublang_getter
        m.compiler_getter = compiler_getter
        m.default_compiler = default_compiler
        m.custom_aliases = None
        m.hint_comments = hint_comments
        m.version = version
        m.lang = lang
        m.fields = {}
        m.at_finish = []
        
    local_renames = global_renames = member_renames = label_renames = None
    
    def add_custom_alias(m, source, target, args):
        if m.custom_aliases is None:
            m.custom_aliases = {}
        m.custom_aliases[source] = (target, args)
    
    def map_aliases(m, name, args):
        while m.custom_aliases and name in m.custom_aliases:
            name, pre_args = m.custom_aliases[name]
            if pre_args:
                if args:
                    args = pre_args + " " + args
                else:
                    args = pre_args
        return name, args.strip()
    
    def get_field(m, name, cls=None):
        """get a custom field, for convenience"""
        if name in m.fields:
            return m.fields[name]
        elif cls is None:
            raise Exception(f"field {name} doesn't exist on ctxt")
        else:
            field = cls()
            m.fields[name] = field
            return field
    
    def set_field(m, name, value):
        """set a custom field, for convenience"""
        m.fields[name] = value
    
    def finish(m):
        at_finish, m.at_finish = m.at_finish, None
        for cb in at_finish:
            cb(ctxt=m)

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

class Focus(Bitmask):
    """Defines what to focus on while minifying"""
    chars = compressed = tokens = ...
    none = 0
