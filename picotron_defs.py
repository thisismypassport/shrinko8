from utils import *
from media_utils import Color
from pico_defs import Language, decode_luastr, encode_luastr, k_palette
from pico_process import ContextBase, Source, get_source_location
import fnmatch

k_palette_64 = [
    *k_palette[:16],
    Color(0x24, 0x63, 0xB0, 0xff),
    Color(0x00, 0xA5, 0xA1, 0xff),
    Color(0x65, 0x46, 0x88, 0xff),
    Color(0x12, 0x53, 0x59, 0xff),
    Color(0x74, 0x2F, 0x29, 0xff),
    Color(0x45, 0x2D, 0x32, 0xff),
    Color(0xA2, 0x88, 0x79, 0xff),
    Color(0xFF, 0xAC, 0xC5, 0xff),
    Color(0xB9, 0x00, 0x3E, 0xff),
    Color(0xE2, 0x6B, 0x02, 0xff),
    Color(0x95, 0xF0, 0x42, 0xff),
    Color(0x00, 0xB2, 0x51, 0xff),
    Color(0x64, 0xDF, 0xF6, 0xff),
    Color(0xBD, 0x9A, 0xDF, 0xff),
    Color(0xE4, 0x0D, 0xAB, 0xff),
    Color(0xFF, 0x85, 0x57, 0xff),
]

def get_default_picotron_version():
    version_id = 2 # TODO - update as newer versions get more common
    return maybe_int(os.getenv("PICOTRON_VERSION_ID"), version_id)

builtin_globals = {
    "USERDATA", "_G", "_VERSION", "abs", "add",  "all", "apply_delta",
    "assert", "atan2", "blit", "btn", "btnp", "camera", "cd",
    "ceil", "chr", "circ", "circfill", "clear_key", "clip",
    "cls", "cocreate", "collectgarbage", "color", "coresume", "coroutine",
    "cos", "costatus", "count", "cp", "create_delta", "create_gui",
    "create_process", "create_socket", "create_undo_stack", "cursor",
    "date", "debug", "del", "deli", "env", "error", "exit",
    "fetch", "fetch_metadata", "fget", "fillp", "flip", "flr", "foreach",
    "fset", "fstat", "fullpath", "get", "get_clipboard", "get_display",
    "get_draw_target", "get_spr", "getmetatable", "include", "ipairs",
    "key", "keyp", "line", "load", "ls", "map", "math", "max", "memcpy",
    "memmap", "memset", "menuitem", "mget", "mid", "min", "mkdir",
    "mount", "mouse", "mouselock", "mset", "music", "mv", "next",
    "note", "notify", "on_event", "open", "ord", "oval", "ovalfill", "pack",
    "pairs", "pal", "palt", "pcall", "peek", "peek2", "peek4", "peek8",
    "peektext", "pget", "pid", "pod", "poke", "poke2", "poke4", "poke8",
    "print", "printh", "pset", "pwd", "pwf", "rawequal", "rawget",
    "rawlen", "rawset", "readtext", "rect", "rectfill", "reset", "rm",
    "rnd", "rrect", "rrectfill", "select", "send_message", "set",
    "set_clipboard", "set_draw_target", "set_spr", "setmetatable",
    "sfx", "sgn", "sin", "split", "spr", "sqrt", "srand", "sspr", "stat",
    "stop", "store", "store_metadata", "string", "sub", "t", "table",
    "theme", "time", "tline3d", "tokenoid", "tonum", "tonumber", "tostr",
    "tostring", "type", "unmap", "unpack", "unpod", "userdata", "utf8",
    "vec", "vid", "warn", "window", "wrangle_working_file", "yield",
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
    "abs", "add", "attribs", "band", "blit", "bor", "bxor", "clear", "column",
    "convert", "copy", "cross", "distance", "div", "dot", "get", "height",
    "idiv", "lerp", "magnitude", "matmul", "matmul2d", "matmul3d", "max", "min",
    "mod", "mul", "mutate", "peek", "poke", "pow", "row", "set", "sgn", "sgn0",
    "shl", "shr", "sort", "sub", "take", "transpose", "width",
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
    "argv", "parent_pid", "path", "window_attribs",
    # create_gui()
    "child", "clip_to_parent", "draw_all", "el_at_pointer", "el_at_xy",
    "get_keyboard_focus_element", "get_pointer_element", "head",
    "height", "height_rel", "id", "new", "sx", "sy", "t0", "update_all",
    "width", "width_rel", "x", "y", "z",
    # create_gui() meta
    "attach", "attach_button", "attach_field", "attach_pulldown",
    "attach_pulldown_item", "attach_scrollbars", "attach_text_editor",
    "bring_to_front", "detach", "draw", "event", "has_keyboard_focus",
    "new", "push_to_back", "set_keyboard_focus",

    # window attrs
    "x", "y", "z", "dx", "dy", "width", "height", "title", "pauseable",
    "wallpaper", "fullscreen", "tabbed", "show_in_workspace", "autoclose",
    "moveable", "resizeable", "has_frame", "video_mode", "cursor", "squashable",
    # more gui stuff (INCOMPLETE...)
    "action", "divider", "label", "bgcol", "fgcol", "border", "hidden", "ghost",
    "justify", "vjustify", "parent", "child", "min_width", "min_height",
    "squash_to_parent", "confine_to_parent", "squash_to_clip", "confine_to_clip",
    "click", "tap", "drag", "autohide",
    
    # event msgs
    "items", "filename", "attrib", "fullpath",

    # pod metadata
    "created", "modified", "pod_type", "pod_format", "revision", "icon",

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
        def key(m):
            return m.fspath

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
    
    @staticmethod
    def topologic_sort(graph): # should sort by dep order and (TODO) gracefully ignore cycles
        backcount = CounterDictionary()
        for node, deps in graph.items():
            for dep in deps:
                backcount[dep] += 1
        
        next = [node for node in graph if backcount[node] == 0]
        result = []
        while next:
            node = next.pop()
            result.append(node)

            for dep in graph[node]:
                backcount[dep] -= 1
                if backcount[dep] == 0:
                    next.append(dep)
        
        for node, count in backcount.items():
            if count != 0:
                result.append(node)
        
        result.reverse()
        return result

    def sort_root(m, root):
        deps = {}

        for node in root.roots.values():
            node_deps = []

            def find_includes(node):
                # since this is best-effort, we don't check var.reassigned/etc
                if node.type == NodeType.call and node.func.type == NodeType.var and is_root_global_or_builtin_local(node.func) and node.func.var.name == "include":
                    arg = list_get(node.args, 0)
                    if arg.type == NodeType.const and arg.token.type == TokenType.string:
                        include = arg.token.parsed_value
                        # we assume include is an absolute path in the cart (we can't deal with much else)
                        # TODO: could handle . and .. and //, though?
                        deproot = root.roots.get(include)
                        if deproot:
                            node_deps.append(deproot)
                            
            node.traverse_nodes(find_includes, extra=True)
            deps[node] = node_deps

        root.children = m.topologic_sort(deps)

from pico_tokenize import TokenType
from pico_parse import NodeType, is_root_global_or_builtin_local
