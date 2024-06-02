from utils import *
from pico_defs import Language, decode_luastr, encode_luastr
from pico_process import ContextBase, Source, get_source_location
import fnmatch

def get_default_picotron_version():
    version_id = 3 # TODO - update as newer versions get more common
    return maybe_int(os.getenv("PICOTRON_VERSION_ID"), version_id)

builtin_globals = {
    "USERDATA", "_G", "_VERSION", "_fetch_remote_result",
    "_get_key_from_scancode", "_process_event_messages",
    "_strindex", "_update_buttons", "abs", "add", "all",
    "apply_delta", "assert", "atan2", "blit", "btn", "btnp", "camera",
    "cd", "ceil", "chr", "circ", "circfill", "clear_key", "clip",
    "cls", "cocreate", "collectgarbage", "color", "coresume", "coroutine",
    "cos", "costatus", "count", "cp", "create_delta", "create_gui",
    "create_meta_key", "create_process", "create_undo_stack", "cursor",
    "date", "debug", "del", "deli", "dtime", "env", "error", "exit",
    "fetch", "fetch_metadata", "fget", "fillp", "flip", "flr", "foreach",
    "fset", "fstat", "fullpath", "get", "get_clipboard", "get_display",
    "get_draw_target", "get_spr", "getmetatable", "include", "ipairs",
    "key", "keyp", "line", "load", "ls", "map", "math", "max", "memcpy",
    "memmap", "memset", "menuitem", "mget", "mid", "min", "mkdir",
    "mount", "mouse", "mouselock", "mset", "music", "mv", "next",
    "note", "notify", "on_event", "ord", "oval", "ovalfill", "pack",
    "pairs", "pal", "palt", "pcall", "peek", "peek2", "peek4", "peek8",
    "peektext", "pget", "pid", "pod", "poke", "poke2", "poke4", "poke8",
    "print", "printh", "pset", "pwd", "pwf", "rawequal", "rawget",
    "rawlen", "rawset", "readtext", "rect", "rectfill", "reset",
    "rm", "rnd", "select", "send_message", "set", "set_clipboard",
    "set_draw_target", "set_spr", "setmetatable", "sfx", "sgn", "sin",
    "split", "spr", "sqrt", "srand", "sspr", "stat", "stop", "store",
    "store_metadata", "string", "sub", "t", "table", "theme", "time",
    "tline3d", "tokenoid", "tonum", "tonumber", "tostr", "tostring",
    "type", "unmap", "unpack", "unpod", "userdata", "utf8", "vec",
    "vid", "warn", "window", "wrangle_working_file", "yield",
}

# subset of builtins that may call user code before returning, NOT including far-fetched stuff like metamethods
# (builtins included here must also be in builtin_globals)
builtins_with_callbacks = {
    "coresume", "foreach", "yield",
    "create_process", "include", "load",
    # TODO: any others?
}
    
builtin_callbacks = {
    "_init", "_draw", "_update",
    # TODO: any others?
}

# TODO: there are likely tons more not covered here...
builtin_members = {
    # USERDATA
    "add", "attribs", "band", "bor", "bxor", "clear", "convert",
    "copy", "cross", "distance", "div", "dot", "get", "height", "magnitude",
    "matmul", "matmul2d", "matmul3d", "mod", "mul", "set", "shl",
    "shr", "sort", "sub", "transpose", "width",
    # coroutine
    "close", "create", "isyieldable", "resume", "running", "status",
    "wrap", "yield",
    # debug
    "debug", "gethook", "getinfo", "getlocal", "getmetatable", "getregistry",
    "getupvalue", "getuservalue", "setcstacklimit", "sethook", "setlocal",
    "setmetatable", "setupvalue", "setuservalue", "traceback", "upvalueid",
    "upvaluejoin",
    # math
    "abs", "acos", "asin", "atan", "ceil", "cos", "deg", "exp", "floor",
    "fmod", "huge", "log", "max", "maxinteger", "min", "mininteger",
    "modf", "pi", "rad", "random", "randomseed", "sin", "sqrt", "tan",
    "tointeger", "type", "ult",
    # string
    "basename", "byte", "char", "dirname", "dump", "ext", "find",
    "format", "gmatch", "gsub", "hloc", "len", "lower", "match",
    "pack", "packsize", "path", "rep", "reverse", "sub", "unpack",
    "upper",
    # table
    "concat", "insert", "move", "pack", "remove", "unpack",
    # utf8
    "char", "charpattern", "codepoint", "codes", "len", "offset",

    # env()
    "argv", "parent_pid", "prog_name", "title", "window_attribs",
    # create_gui()
    "child", "clip_to_parent", "draw_all", "el_at_pointer", "el_at_xy",
    "get_keyboard_focus_element", "get_pointer_element", "head",
    "height", "height_rel", "id", "new", "sx", "sy", "t0", "update_all",
    "width", "width_rel", "x", "y", "z",

    # window attrs
    "x", "y", "z", "dx", "dy", "width", "height",
    "wallpaper", "fullscreen", "tabbed", "show_in_workspace",
    "moveable", "resizeable", "has_frame", "video_mode",

    # pod metadata
    "created", "modified", "pod_format", "revision",

    # pack()
    "n",
    # metamethods
    "__add", "__band", "__bnot", "__bor", "__bxor", "__close",
    "__call", "__concat", "__div", "__eq", "__gc", "__idiv",
    "__index", "__lt", "__le", "__len", "__metatable", "__mod",
    "__mode", "__mul", "__name", "__newindex", "__pairs", "__pow",
    "__shl", "__shr", "__sub", "__tostring", "__unm",
}

class PicotronContext(ContextBase):
    """Specialization of ContextBase to picotron"""
    def __init__(m, **opts):
        super().__init__(Language.picotron, builtin_globals, set(), builtins_with_callbacks, builtin_callbacks, builtin_members, **opts)

class Cart64Glob:
    def __init__(m, patterns):
        m.regexes = []
        for pattern in patterns:
            action = True
            if pattern.startswith("!"):
                action = False
                pattern = pattern[1:]
            m.regexes.append((re.compile(fnmatch.translate(pattern)), action))

    def matches(m, path):
        result = False
        for regex, action in m.regexes:
            if regex.match(path):
                result = action
                if not result:
                    return False
        return result     
    
class Cart64Source(Source):
    """The source of a picotron cart, consists of multiple sub-sources, one for each source file"""

    class SubSource(Source):
        def __init__(m, parent, fspath, file):
            m.parent, m.fspath, m.file = parent, fspath, file
            # no super().__init__ - we override with properties
        
        @property
        def path(m):
            return m.parent.path + "/" + m.fspath

        def get_location(m, idx, tabs=False): # (0-based)
            return get_source_location(m.path, m.text, idx, m.file.line)

        @property
        def text(m):
            return decode_luastr(m.file.raw_payload)

        @text.setter
        def text(m, val):
            m.file.raw_payload = encode_luastr(val)
        
    def __init__(m, cart, code_patterns=None):
        m.cart = cart
        # no super().__init__ - we override with properties
        m.subsources = []
        glob = Cart64Glob(code_patterns) if code_patterns else None
        for path, file in m.cart.files.items():
            if file.is_raw: # else, definitely not a source file
                if glob.matches(path) if glob else path.endswith(".lua"):
                    m.subsources.append(m.SubSource(m, path, file))

    @property
    def path(m):
        return m.cart.path
        
    @property
    def text(m):
        fail("super-source misuse")
        
    is_super = True
    def __iter__(m):
        return iter(m.subsources)
