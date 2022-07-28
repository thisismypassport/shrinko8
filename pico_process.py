from utils import *
from pico_defs import to_pico_chars, from_pico_chars
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

global_callbacks = {
    "_init", "_draw", "_update", "_update60",
}

member_strings = {
    "n",
    "__index", "__newindex", "__len", "__eq", "__lt", "__le",
    "__add", "__sub", "__mul", "__div", "__idiv", "__mod",
    "__pow", "__and", "__or", "__xor", "__shl", "__shr",
    "__lshr", "__rotl", "__rotr", "__concat", "__unm", "__not",
    "__peek", "__peek2", "__peek4", "__call", "__tostring",
    "__pairs", "__ipairs", "__metatable", "__gc", "__mode",
}

keywords = {
    "and", "break", "do", "else", "elseif", "end", "false", 
    "for", "function", "goto", "if", "in", "local", "nil", 
    "not", "or", "repeat", "return", "then", "true", "until",
    "while"
}

class PicoSource: # keep this light - created for temp. tokenizations
    __slots__ = ("name", "text")

    def __init__(m, name, text):
        m.name, m.text = name, text
        
    def get_name_line_col(m, idx):
        start = 0
        line = 0

        while start < idx:
            end = m.text.find("\n", start)
            if end < 0 or end >= idx:
                break
            line += 1
            start = end + 1
        
        return m.name, line, idx - start

class PicoComplexSource(PicoSource):
    def __init__(m, name, text, mappings=(), errors=()):
        m.cart = None
        super().__init__(name, text)
        m.mappings = mappings
        m.errors = errors

    def get_name_line_col(m, idx):
        name, line, col = super().get_name_line_col(idx)

        real_name, real_line = name, line
        for mapping in m.mappings:
            if line >= mapping.line:
                real_name = mapping.name
                real_line = line - mapping.line + mapping.real_line
        
        return real_name, real_line, col

    @property
    def text(m):
        return m.cart.code if m.cart else m._text

    @text.setter
    def text(m, v):
        if m.cart:
            m.cart.set_code(v)
        else:
            m._text = v

    def tie_to(m, cart):
        cart.set_code(m.text)
        m.cart = cart

class VarKind(Enum):
    values = ("local", "global_", "member")
    
class VarBase():
    def __init__(m, name):
        m.name = name
        m.keys_kind = None

class Local(VarBase):
    def __init__(m, name, scope, implicit):
        super().__init__(name)
        m.scope, m.implicit = scope, implicit

class Global(VarBase):
    pass

class Scope:
    def __init__(m, parent=None, depth=0, funcdepth=0):
        m.parent = parent
        m.depth = depth
        m.funcdepth = funcdepth
        m.items = {}

    def add(m, var):
        m.items[var.name] = var

    def find(m, item):
        if item in m.items:
            return m.items[item]
        elif m.parent:
            return m.parent.find(item)

class PicoContext:
    def __init__(m, deprecated=True, undocumented=True, patterns=True, srcmap=None, extra_globals=set()):
        funcs = set(main_globals)
        if deprecated:
            funcs |= deprecated_globals
        if undocumented:
            funcs |= undocumented_globals
        if patterns:
            funcs |= pattern_globals
        funcs |= extra_globals

        m.globals = funcs

        m.srcmap = [] if srcmap else None

class TokenNodeBase:
    def __init__(m):
        m.parent, m.children = None, ()
    
    def find_parent(m, type):
        parent = m.parent
        while parent and parent.type != type:
            parent = parent.parent
        return parent

    def _sibling(m, delta):
        parent = m.parent
        i = parent.children.index(m) + delta
        return list_get(parent.children, i)

    def next_sibling(m): return m._sibling(1)
    def prev_sibling(m): return m._sibling(-1)

    def _adjacent(m, delta):
        while m:
            sib = m._sibling(delta)
            if sib:
                return sib
            m = m.parent
        return None

    def _adjacent_token(m, delta):
        i = 0 if delta > 0 else -1
        m = m._adjacent(delta)
        while isinstance(m, Node):
            if m.children:
                m = m.children[i]
            else:
                m = m._adjacent(delta)
        return m if m else Token.dummy(None)

    def next_token(m): return m._adjacent_token(1)
    def prev_token(m): return m._adjacent_token(-1)

    def traverse_nodes(m, pre=None, post=None, extra=False):
        if pre: pre(m)
        for child in m.children:
            if isinstance(child, Node):
                child.traverse_nodes(pre, post, extra)
        if extra and hasattr(m, "extra_children"):
            for child in m.extra_children:
                child.traverse_nodes(pre, post, extra)
        if post: post(m)

    def traverse_tokens(m, visit):
        for child in m.children:
            if isinstance(child, Node):
                child.traverse_tokens(visit)
            else:
                visit(child)

class TokenType(Enum):
    values = ("number", "string", "ident", "keyword", "punct", "comment", "lint")

class Token(TokenNodeBase):
    def __init__(m, type, value, source=None, idx=None, endidx=None, vline=None):
        super().__init__()
        m.type, m.value, m.source, m.idx, m.endidx, m.vline = type, value, source, idx, endidx, vline

    @classmethod
    def dummy(m, source, idx=None):
        if idx is None:
            idx = len(source.text) if source else 0
        return Token(None, None, source, idx, idx, 0)

    @property
    def fake(m):
        return m.type in (TokenType.lint, TokenType.comment)

class Error:
    def __init__(m, msg, token):
        m.msg, m.token = msg, token

    def __str__(m):
        token = m.token
        name, line, col = token.source.get_name_line_col(token.idx) if token.source else ("???", 0, 0)
        return "%s(%s:%s) - %s" % (name, line + 1, col + 1, m.msg)

define_use_re = re.compile(r"\$\[(\w*)\]")
define_cond_re = re.compile(r"\$\[(\w+)\[(=*)\[(.*?)\]\2\]\]")
p8_section_re = re.compile(r"^__\w+__\s*$")

def read_code(filename, defines=None, pp_handler=None, pp_inline=False, fail=True):
    lines = []
    defines = defines.copy() if defines else {}
    ppstack = []
    ppline = None
    active = True
    mappings = []
    errors = []

    def add_error(ctxt, error):
        name, i = ctxt
        errors.append("%s(%s) - %s" % (name, i, error))

    def get_active():
        return ppstack[-1] if ppstack else True

    def get_defined(m, ctxt):
        key = m.group(1)
        if not key:
            return "$[" # escape $[ with $[]
        elif key in defines:
            return defines[key]
        else:
            if pp_handler:
                pp_result = pp_handler(op="$" + key, args=(), ppline=m.group(), active=True, lines=lines)
                if isinstance(pp_result, str):
                    return pp_result
            
            add_error(ctxt, "Undefined: %s" % key)
            return ""

    def get_conditional(m, ctxt):
        key = m.group(1)
        if key in defines:
            return m.group(3)
        else:
            if pp_handler:
                pp_result = pp_handler(op="$" + key, args=[m.group(3)], ppline=m.group(), active=True, lines=lines)
                if isinstance(pp_result, str):
                    return pp_result
            return ""
    
    def add_code_line(name, i, line, raw=False):
        nonlocal active, ppline
        ctxt = (name, i)

        if ppline:
            line, ppline = ppline + line, None

        lstrip = line.lstrip()
        if lstrip.startswith("#") and not raw:
            if lstrip.startswith("##"): # escape starting # with ##
                line = line[:-len(lstrip)] + lstrip[1:]
                return add_code_line(name, i, line, raw=True) 

            if line.endswith("\\\n"):
                ppline = line[:-2] + "\n"
                return

            args = line.split()
            op = args[0] if args else ""

            if op == "#" and len(args) == 1:
                pass

            elif op == "#include" and len(args) == 2:
                if active:
                    add_code_file(args[1])

            elif op == "#define" and len(args) >= 2:
                if active:
                    value = line.split(None, 2)[2].rstrip() if len(args) > 2 else ""
                    defines[args[1]] = value

            elif op == "#undef" and len(args) == 2:
                if active:
                    del defines[args[1]]

            elif op == "#ifdef" and len(args) == 2:
                active &= args[1] in defines
                ppstack.append(active)

            elif op == "#ifndef" and len(args) == 2:
                active &= args[1] not in defines
                ppstack.append(active)

            elif op == "#else" and len(args) == 1 and ppstack:
                old_active = ppstack.pop()
                active = get_active() and not old_active
                ppstack.append(active)

            elif op == "#endif" and len(args) == 1 and ppstack:
                ppstack.pop()
                active = get_active()

            elif not (pp_handler and pp_handler(op=op, args=args, ppline=line, active=active, lines=lines)):
                add_error(ctxt, "Invalid preprocessor line: %s" % line)

            mappings.append(Dynamic(line=len(lines), name=name, real_line=i + 1))

        elif active:
            if pp_inline: # needs rework, too intrusive
                line = define_cond_re.sub(lambda m: get_conditional(m, ctxt), line)
                line = define_use_re.sub(lambda m: get_defined(m, ctxt), line) # put this regex last (handles escape)

            lines.append(to_pico_chars(line))

    def add_code_file(name):
        data = file_read_text(path_join(root_dir, name))
        file_lines = data.splitlines(keepends=True)

        start = 0
        while start < len(file_lines) and file_lines[start].strip() != "__lua__":
            start += 1
        if start < len(file_lines):
            start += 1

            end = start
            while end < len(file_lines) and not p8_section_re.match(file_lines[end]):
                end += 1
        else:
            start, end = 0, len(file_lines) # treat as pure-code file
            
        mappings.append(Dynamic(line=len(lines), name=name, real_line=start))

        i = start
        for line in file_lines[start:end]:
            add_code_line(name, i, line)
            i += 1
    
    root_dir = path_dirname(filename)
    add_code_file(path_basename(filename))

    if fail and errors:
        raise Exception("\n".join(errors))

    text = "".join(lines)
    return PicoComplexSource(path_basename(filename), text, mappings, errors)

k_lint_prefix = "lint:"
k_keep_prefix = "keep:"

k_lint_func_prefix = "func::"
k_lint_count_stop = "count::stop"

k_wspace = " \t\r\n"

def is_ident_char(ch):
    return '0' <= ch <= '9' or 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch == '_' or ch >= chr(0x80)

def tokenize(source):
    text = source.text
    idx = 0
    vline = 0
    tokens = []
    errors = []
    next_var_kind = None
    next_keys_kind = None
    next_func_kind = None

    def peek(off=0):
        i = idx + off
        return text[i] if 0 <= i < len(text) else ''

    def take():
        nonlocal idx
        ch = peek()
        idx += 1
        return ch

    def accept(ch,):
        nonlocal idx
        if peek() == ch:
            idx += 1
            return True
        return False

    def accept_one_of(*chs):
        nonlocal idx
        if peek() in chs:
            idx += 1
            return True
        return False

    def add_token(type, start, end_off=0, value=None):
        end = idx + end_off
        if value is None:
            value = text[start:end]
        tokens.append(Token(type, value, source, start, end, vline))
        add_token_kinds()

    def add_error(msg, off=-1):
        errors.append(Error(msg, Token.dummy(source, idx + off)))

    def add_token_kinds():
        nonlocal next_var_kind, next_keys_kind, next_func_kind
        if next_var_kind != None:
            tokens[-1].var_kind = next_var_kind
            next_var_kind = None
        if next_keys_kind != None:
            tokens[-1].keys_kind = next_keys_kind
            next_keys_kind = None
        if next_func_kind != None:
            tokens[-1].func_kind = next_func_kind
            next_func_kind = None

    def process_comment(orig_idx, comment, isblock):
        if comment.startswith(k_lint_prefix):
            lints = [v.strip() for v in comment[len(k_lint_prefix):].split(",")]
            add_token(TokenType.lint, orig_idx, value=lints)

            for lint in lints:
                if lint.startswith(k_lint_func_prefix):
                    nonlocal next_func_kind
                    next_func_kind = lint[len(k_lint_func_prefix):]

        elif comment.startswith(k_keep_prefix):
            keep_comment = comment[len(k_keep_prefix):].rstrip()
            add_token(TokenType.comment, orig_idx, value=keep_comment)

        elif isblock:
            nonlocal next_var_kind, next_keys_kind
            if comment in ("global", "nameof"): # nameof is deprecated
                next_var_kind = VarKind.global_
            elif comment in ("member", "memberof"): # memberof is deprecated
                next_var_kind = VarKind.member
            elif comment in ("preserve", "string"):
                next_var_kind = False
            elif comment == "global-keys":
                next_keys_kind = VarKind.global_
            elif comment == "member-keys":
                next_keys_kind = VarKind.member
            elif comment in ("preserve-keys", "string-keys"):
                next_keys_kind = False

    def tokenize_line_comment():
        nonlocal vline
        orig_idx = idx
        while take() not in ('\n', ''): pass
        vline += 1

        process_comment(orig_idx, text[orig_idx:idx], isblock=False)

    def tokenize_long_brackets(off):
        nonlocal idx
        idx += off
        orig_idx = idx

        if accept('['):
            pad_idx = idx
            while accept('='): pass
            pad = text[pad_idx:idx]

            if accept('['):
                start_i = idx
                end_i = text.find("]%s]" % pad, idx)
                if end_i >= 0:
                    idx = end_i + len(pad) + 2
                else:
                    idx = len(text)
                    add_error("Unterminated long brackets", orig_idx - idx)

                return True, orig_idx, start_i, end_i
                
        return False, orig_idx, None, None

    def tokenize_long_comment():
        nonlocal idx
        ok, orig_idx, start, end = tokenize_long_brackets(0)
        if ok:
            process_comment(orig_idx, text[start:end], isblock=True)
        else:
            idx = orig_idx
        return ok

    def tokenize_number(off):
        nonlocal idx
        idx += off
        orig_idx = idx

        ch = peek()
        if ch == '0' and peek(1) in ('b', 'B'):
            idx += 2
            digits = "01"
        elif ch == '0' and peek(1) in ('x', 'X'):
            idx += 2
            digits = "0123456789aAbBcCdDeEfF"
        else:
            digits = "0123456789"

        allow_dot = True
        while True:
            ch = peek()
            if ch and ch in digits:
                idx += 1
            elif allow_dot and ch == '.':
                allow_dot = False
                idx += 1
            else:
                break

        add_token(TokenType.number, orig_idx)

    def tokenize_ident(off):
        nonlocal idx
        idx += off
        orig_idx = idx
        
        while is_ident_char(peek()):
            idx += 1
            
        if text[orig_idx:idx] in keywords:
            add_token(TokenType.keyword, orig_idx)
        else:
            add_token(TokenType.ident, orig_idx)

    def tokenize_string(off):
        nonlocal idx
        orig_idx = idx + off
        idx = orig_idx + 1
        quote = text[orig_idx]

        while True:
            ch = take()
            if ch in ('\n', ''):
                add_error("Unterminated_string")
                break
            elif ch == '\\':
                if accept('z'): # skip line breaks
                    while peek() in k_wspace:
                        take()
                else:
                    take() # at least
            elif ch == quote:
                break

        add_token(TokenType.string, orig_idx)

    def tokenize_long_string(off):
        ok, orig_idx, _, _ = tokenize_long_brackets(off)
        if ok:
            add_token(TokenType.string, orig_idx)
        else:
            add_error("Invalid long brackets")

    while idx < len(text):
        ch = take()

        if ch in k_wspace: # whitespace
            if ch == "\n":
                vline += 1

        elif ch == '-' and accept('-'): # comment
            if not tokenize_long_comment():
                tokenize_line_comment()

        elif '0' <= ch <= '9' or (ch == '.' and '0' <= peek() <= '9'): # number
            tokenize_number(-1)

        elif is_ident_char(ch): # identifier
            tokenize_ident(-1)

        elif ch in ('"', "'"): # string
            tokenize_string(-1)

        elif ch == '[' and accept_one_of('=', '['): # long string
            tokenize_long_string(-2)

        elif ch in "+-*/\\%&|^<>=~#()[]{};,?@$.:": # punctuation
            orig_idx = idx - 1
            if ch in ".:^<>" and accept(ch):
                if ch in ".>" and accept(ch):
                    if ch == ">": accept('=')
                elif ch in "<>" and accept(">" if ch == "<" else "<"):
                    accept('=')
                elif ch in ".^<>":
                    accept('=')
            elif ch in "+-*/\\%&|^<>=~":
                accept('=')
            add_token(TokenType.punct, orig_idx)

        elif ch == '!' and accept('='): # alt. punctuation
            add_token(TokenType.punct, idx - 2)

        else:
            add_error("invalid character")
        
    return tokens, errors

def count_tokens(tokens):
    count = 0
    for i, token in enumerate(tokens):
        if token.fake:
            if token.type == TokenType.lint and k_lint_count_stop in token.value:
                break
            continue

        if token.value in (",", ".", ":", ";", "::", ")", "]", "}", "end", "local"):
            continue

        if token.value in ("-", "~") and i+1 < len(tokens) and tokens[i+1].type == TokenType.number and \
            i-1 >= 0 and tokens[i-1].type not in (TokenType.number, TokenType.string, TokenType.ident) and \
            tokens[i-1].value not in (")", "]", "}", ";", "end"):
            continue

        count += 1
    return count

class NodeType(Enum):
    values = ("var", "index", "member", "const", "group", "unary_op", "binary_op", "call",
              "table", "table_index", "table_member", "varargs", "assign", "op_assign",
              "local", "function", "if_", "elseif", "else_", "while_", "repeat", "until",
              "for_", "for_in", "return_", "break_", "goto", "label", "print", "block", "do")

class Node(TokenNodeBase):
    def __init__(m, type, children, **kwargs):
        super().__init__()

        if children:
            first, last = children[0], children[-1]
            m.source, m.idx, m.endidx = first.source, first.idx, last.endidx
        else:
            m.source, m.idx, m.endidx = None, None, None

        m.type, m.children, m.value, m.scopespec = type, children, None, None
        m.__dict__.update(kwargs)

        for child in children:
            child.parent = m

    @property
    def start_scope(m):
        if m.scopespec:
            if isinstance(m.scopespec, Scope):
                return m.scopespec
            elif m.scopespec[0]:
                return m.scopespec[1]

    @property
    def end_scopes(m):
        if m.scopespec:
            if isinstance(m.scopespec, Scope):
                return (m.scopespec,)
            elif not m.scopespec[0]:
                return m.scopespec[1]
        return ()
    
class ParseError(Exception):
    pass

k_unary_ops = {
    "-", "~", "not", "#", "@", "%", "$",
}

k_unary_ops_prec = 11

k_binary_op_precs = {
    "or": 1, "and": 2,
    "!=": 3, "~=": 3, "==": 3, "<": 3, "<=": 3, ">": 3, ">=": 3,
    "|": 4, "^^": 5, "&": 6,
    "<<": 7, ">>": 7, ">>>": 7, ">><": 7, "<<>": 7,
    "..": 8,
    "+": 9, "-": 9,
    "*": 10, "/": 10, "\\": 10, "%": 10,
    "^": 12,
}

k_right_binary_ops = {
    "^", ".."
}

k_block_ends = ("end", "else", "elseif", "until")

def parse(source, tokens):
    idx = 0
    depth = -1
    funcdepth = 0
    scope = Scope(None, depth, funcdepth)
    errors = []
    globals = LazyDict(lambda key: Global(key))

    tokens = [t for t in tokens if not t.fake]
    
    scope.add(Local("_ENV", scope, True))
   
    def peek(off=0):
        i = idx + off
        return tokens[i] if 0 <= i < len(tokens) else Token.dummy(source)
    
    def take():
        nonlocal idx
        token = peek()
        idx += 1
        return token
    
    def accept(value, tokens=None):
        nonlocal idx
        if peek().value == value:
            if e(tokens):
                tokens.append(peek())
            idx += 1
            return True
        return False

    def add_error(msg, off=0, fail=False):
        err = Error(msg, peek(off))
        errors.append(err)
        if fail:
            raise ParseError()

    def require(value, tokens=None):
        if not accept(value, tokens):
            add_error("expected '%s'" % value, fail=True)
        return peek(-1)

    def require_ident(tokens=None):
        nonlocal idx
        if peek().type == TokenType.ident:
            if e(tokens):
                tokens.append(peek())
            idx += 1
            return peek(-1)
        add_error("identifier expected", fail=True)

    def parse_var(token=None, newscope=None, member=False, implicit=False):
        token = token or require_ident()
        name = token.value

        var = None
        kind = VarKind.local
        if newscope:
            var = Local(name, newscope, implicit)
        elif member:
            kind = VarKind.member
        else:
            if e(scope):
                var = scope.find(name)
            if not var:
                kind = VarKind.global_
                var = globals[name]

        var_kind = getattr(token, "var_kind", None)
        if var and hasattr(token, "keys_kind"):
            var.keys_kind = token.keys_kind

        return Node(NodeType.var, [token], name=name, kind=kind, var_kind=var_kind, var=var, new=bool(newscope), parent_scope=scope)
    
    def parse_function(stmt=False, local=False):
        nonlocal scope, funcdepth
        tokens = [peek(-1)]
        extra_children = None
        func_kind = getattr(tokens[0], "func_kind", None)
        
        target, name = None, None
        funcscope = Scope(scope, depth + 1, funcdepth + 1)

        params = []
        if stmt:
            if local:
                target = parse_var(newscope=scope)
                scope.add(target.var)
                name = target.name
            else:
                target = parse_var()
                name = target.name

                while accept("."):
                    token = peek(-1)
                    key = parse_var(member=True)
                    target = Node(NodeType.member, [target, token, key], key=key, child=target, method=False)
                    name += "." + key.name

                if accept(":"):
                    token = peek(-1)
                    key = parse_var(member=True)
                    target = Node(NodeType.member, [target, token, key], key=key, child=target, method=True)
                    name += ":" + key.name

                    params.append(parse_var(token=Token(TokenType.ident, "self"), newscope=funcscope, implicit=True))
                    extra_children = [params[-1]]

            tokens.append(target)

        require("(", tokens)
        if not accept(")", tokens):
            while True:
                if accept("..."):
                    params.append(Node(NodeType.varargs, [peek(-1)]))
                else:
                    params.append(parse_var(newscope=funcscope))
                tokens.append(params[-1])

                if accept(")", tokens):
                    break
                require(",", tokens)

        for param in params:
            if param.type == NodeType.var:
                funcscope.add(param.var)

        funcdepth += 1
        scope = funcscope
        body = parse_block()
        tokens.append(body)
        require("end", tokens)
        scope = scope.parent
        funcdepth -= 1

        funcnode = Node(NodeType.function, tokens, target=target, params=params, body=body, name=name, scopespec=funcscope, kind=func_kind)
        if extra_children:
            funcnode.extra_children = extra_children
        return funcnode

    def parse_table():
        tokens = [peek(-1)]
        keys_kind = getattr(tokens[0], "keys_kind", None)
        
        items = []
        while not accept("}", tokens):
            if accept("["):
                open = peek(-1)
                key = parse_expr()
                close = require("]")
                eq = require("=")
                value = parse_expr()
                items.append(Node(NodeType.table_index, [open, key, close, eq, value], key=key, value=value))

            elif peek(1).value == "=":
                key = parse_var(member=True)
                eq = require("=")
                value = parse_expr()
                items.append(Node(NodeType.table_member, [key, eq, value], key=key, value=value))
                
            else:
                items.append(parse_expr())
                
            tokens.append(items[-1])

            if accept("}", tokens):
                break

            if not accept(";", tokens):
                require(",", tokens)

        return Node(NodeType.table, tokens, items=items, keys_kind=keys_kind)

    def parse_call(expr, extra_arg=None):
        tokens = [expr, peek(-1)]
        args = []

        if extra_arg:
            args.append(extra_arg) # not a direct token

        if not accept(")", tokens):
            while True:
                args.append(parse_expr())
                tokens.append(args[-1])

                if accept(")", tokens):
                    break
                require(",", tokens)
        
        return Node(NodeType.call, tokens, func=expr, args=args)

    def parse_const_var_kind(node):
        token = node.token
        if getattr(token, "var_kind", None):
            node.extra_names = token.value[1:-1].split(",")
            node.extra_children = []
            for i, value in enumerate(node.extra_names):
                subtoken = Token(TokenType.ident, value)
                subtoken.var_kind = token.var_kind
                subnode = parse_var(token=subtoken, member=True)
                subnode.parent = node
                subnode.extra_i = i
                node.extra_children.append(subnode)
        return node

    def parse_core_expr():
        token = peek()
        value = take().value
        if value == None:
            add_error("unexpected end of input", fail=True)
        elif value in ("nil", "true", "false") or token.type in (TokenType.number, TokenType.string):
            return parse_const_var_kind(Node(NodeType.const, [token], token=token))
        elif value == "{":
            return parse_table()
        elif value == "(":
            expr = parse_expr()
            close = require(")")
            return Node(NodeType.group, [token, expr, close], child=expr)
        elif value in k_unary_ops:
            expr = parse_expr(k_unary_ops_prec)
            return Node(NodeType.unary_op, [token, expr], child=expr, op=value)
        elif value == "function":
            return parse_function()
        elif value == "...":
            return Node(NodeType.varargs, [token])
        elif token.type == TokenType.ident:
            return parse_var(token=token)
        else:
            add_error("unknown expression", fail=True)

    def compare_prec(op, prec):
        return (prec == None) or ((prec <= k_binary_op_precs[op]) if op in k_right_binary_ops else (prec < k_binary_op_precs[op]))

    def parse_expr(prec=None):
        expr = parse_core_expr()
        while True:
            nonlocal idx
            token = peek()
            value = take().value
            if value == ".":
                var = parse_var(member=True)
                expr = Node(NodeType.member, [expr, token, var], key=var, child=expr, method=False)
            elif value == "[":
                index = parse_expr()
                close = require("]")
                expr = Node(NodeType.index, [expr, token, index, close], key=index, child=expr)
            elif value == "(":
                expr = parse_call(expr)
            elif value == "{" or peek(-1).type == TokenType.string:
                idx -= 1
                arg = parse_core_expr()
                expr = Node(NodeType.call, [expr, arg], func=expr, args=[arg])
            elif value == ":":
                var = parse_var(member=True)
                expr = Node(NodeType.member, [expr, token, var], key=var, child=expr, method=True)
                if peek().value == "{" or peek().type == TokenType.string:
                    arg = parse_core_expr()
                    expr = Node(NodeType.call, [expr, arg], func=expr, args=[var, arg])
                else:
                    require("(")
                    expr = parse_call(expr, extra_arg=var)
            elif value in k_binary_op_precs and compare_prec(value, prec):
                other = parse_expr(k_binary_op_precs[value])
                expr = Node(NodeType.binary_op, [expr, token, other], left=expr, right=other, op=value)
            else:
                idx -= 1
                return expr

    def parse_list(tokens, func):
        list = [func()]
        tokens.append(list[-1])
        while accept(",", tokens):
            list.append(func())
            tokens.append(list[-1])
        return list

    def parse_if(type=NodeType.if_):
        tokens = [peek(-1)]
        cond = parse_expr()
        tokens.append(cond)
        else_ = None
        short = False

        if accept("then", tokens):
            then = parse_block()
            tokens.append(then)

            if accept("else"):
                else_tokens = [peek(-1)]
                else_body = parse_block()
                else_tokens.append(else_body)
                require("end", else_tokens)
                else_ = Node(NodeType.else_, else_tokens, body=else_body, short=False)
                tokens.append(else_)

            elif accept("elseif"):
                else_ = parse_if(NodeType.elseif)
                tokens.append(else_)

            else:
                require("end", tokens)
                
        elif peek(-1).value == ")":
            vline = peek(-1).vline
            then = parse_block(vline=vline)
            tokens.append(then)
            short = True

            if peek().vline == vline and accept("else"):
                else_tokens = [peek(-1)]
                else_body = parse_block(vline=vline)
                else_tokens.append(else_body)
                else_ = Node(NodeType.else_, else_tokens, body=else_body, short=True)
                tokens.append(else_)

        else:
            add_error("then or shorthand required", fail=True)
            
        return Node(type, tokens, cond=cond, then=then, else_=else_, short=short)

    def parse_while():
        tokens = [peek(-1)]
        cond = parse_expr()
        tokens.append(cond)
        short = False

        if accept("do", tokens):
            body = parse_block()
            tokens.append(body)
            require("end", tokens)
        elif peek(-1).value == ")":
            body = parse_block(vline=peek(-1).vline)
            tokens.append(body)
            short = True
        else:
            add_error("do or shorthand required", fail=True)

        return Node(NodeType.while_, tokens, cond=cond, body=body, short=short)

    def parse_repeat():
        tokens = [peek(-1)]
        body = parse_block(until=True)
        tokens.append(body)
        return Node(NodeType.repeat, tokens, body=body, until=body.children[-1])

    def parse_until():
        tokens = []
        require("until", tokens)
        cond = parse_expr()
        tokens.append(cond)
        return Node(NodeType.until, tokens, cond=cond)
        
    def parse_for():
        nonlocal scope
        tokens = [peek(-1)]

        if peek(1).value == "=":
            newscope = Scope(scope, depth + 1, funcdepth)
            target = parse_var(newscope=newscope)
            tokens.append(target)
            require("=", tokens)
            min = parse_expr()
            tokens.append(min)
            require(",", tokens)
            max = parse_expr()
            tokens.append(max)
            step = None
            if accept(",", tokens):
                step = parse_expr()
                tokens.append(step)

            require("do", tokens)
            newscope.add(target.var)

            scope = newscope
            body = parse_block()
            tokens.append(body)
            require("end", tokens)
            scope = scope.parent

            return Node(NodeType.for_, tokens, target=target, min=min, max=max, step=step, body=body, scopespec=newscope)

        else:
            newscope = Scope(scope, depth + 1, funcdepth)
            targets = parse_list(tokens, lambda: parse_var(newscope=newscope))
            require("in", tokens)
            sources = parse_list(tokens, parse_expr)
            require("do", tokens)

            for target in targets:
                newscope.add(target.var)

            scope = newscope
            body = parse_block()
            tokens.append(body)
            require("end", tokens)
            scope = scope.parent

            return Node(NodeType.for_in, tokens, targets=targets, sources=sources, body=body, scopespec=newscope)

    def parse_return(vline):
        tokens = [peek(-1)]
        if peek().value in k_block_ends + (";",) or (e(vline) and peek().vline > vline):
            return Node(NodeType.return_, tokens, rets=[])
        else:
            rets = parse_list(tokens, parse_expr)
            return Node(NodeType.return_, tokens, rets=rets)

    def parse_local():
        nonlocal scope
        tokens = [peek(-1)]
        newscope = Scope(scope, depth, funcdepth)

        if accept("function"):
            scope = newscope
            func = parse_function(stmt=True, local=True)
            tokens.append(func)

            return Node(NodeType.local, tokens, targets=[func.name], sources=[func], scopespec=(True, newscope))

        else:
            targets = parse_list(tokens, lambda: parse_var(newscope=newscope))
            sources = []
            if accept("=", tokens):
                sources = parse_list(tokens, parse_expr)
                
            for target in targets:
                newscope.add(target.var)
            scope = newscope

            return Node(NodeType.local, tokens, targets=targets, sources=sources, scopespec=(True, newscope))

    def parse_assign(first):
        tokens = [first]
        if accept(",", tokens):
            targets = [first] + parse_list(tokens, parse_expr)
        else:
            targets = [first]

        require("=", tokens)
        sources = parse_list(tokens, parse_expr)

        return Node(NodeType.assign, tokens, targets=targets, sources=sources)

    def parse_misc_stmt():
        nonlocal idx
        idx -= 1
        first = parse_expr()
        if peek().value in (",", "="):
            return parse_assign(first)
        elif peek().value and peek().value.endswith("="):
            token = peek()
            op = token.value[:-1]
            idx += 1
            source = parse_expr()
            return Node(NodeType.op_assign, [first, token, source], target=first, source=source, op=op)
        elif first.type == NodeType.call:
            return first
        else:
            add_error("expression has no side-effect")

    def parse_stmt(vline):
        token = peek()
        value = take().value
        if value == ";":
            return None
        elif value == "do":
            body = parse_block()
            end = require("end")
            return Node(NodeType.do, [token, body, end], body=body)
        elif value == "if":
            return parse_if()
        elif value == "while":
            return parse_while()
        elif value == "repeat":
            return parse_repeat()
        elif value == "for":
            return parse_for()
        elif value == "break":
            return Node(NodeType.break_, [token])
        elif value == "return":
            return parse_return(vline)
        elif value == "local":
            return parse_local()
        elif value == "goto":
            label = require_ident()
            return Node(NodeType.goto, [token, label], label=label)
        elif value == "::":
            label = require_ident()
            end = require("::")
            return Node(NodeType.label, [token, label, end], label=label)
        elif value == "function":
            return parse_function(stmt=True)
        elif value == "?":
            tokens = [token]
            args = parse_list(tokens, parse_expr)
            return Node(NodeType.print, tokens, args=args)
        else:
            return parse_misc_stmt()

    def parse_block(vline=None, until=False):
        nonlocal scope, depth
        oldscope = scope
        start = peek()
        depth += 1

        stmts = []
        tokens = []
        while e(peek().type):
            if e(vline) and peek().vline > vline:
                break

            if peek().value in k_block_ends:
                break
            
            stmt = parse_stmt(vline)
            if stmt:
                stmts.append(stmt)
                tokens.append(stmt)
            else:
                tokens.append(peek(-1))

        if until:
            tokens.append(parse_until())

        depth -= 1
        scopes = []
        while scope != oldscope:
            scopes.append(scope)
            scope = scope.parent
        
        return Node(NodeType.block, tokens, stmts=stmts, scopespec=(False, scopes))

    def parse_root():
        root = parse_block()
        root.globals = globals
        if peek().type != None:
            add_error("Expected end of input")
        assert scope.parent is None
        #verify_parse(root) # DEBUG
        return root

    """def verify_parse_rec(node):
        if isinstance(node, Node):
            for child in node.children:
                verify_parse_rec(child)
        else:
            assert isinstance(node, Token)
            nonlocal idx
            if node.source != None:
                assert node == tokens[idx]
                idx += 1

    def verify_parse(root):
        nonlocal idx
        idx = 0
        verify_parse_rec(root)
        assert idx == len(tokens)"""

    try:
        return parse_root(), errors
    except ParseError:
        return None, errors

def to_fixnum(value):
    return int(value * (1 << 16)) & 0xffffffff

def parse_fixnum(str):
    str = str.lower()
    neg = False
    if str.startswith("-"):
        str = str[1:]
        neg = True

    digits = "0123456789"
    if str.startswith("0x"):
        digits += "abcdef"
        str = str[2:]
    elif str.startswith("0b"):
        digits = "01"
        str = str[2:]
    base = len(digits)

    value = 0
    while str and str[0] in digits:
        value = (value * base) + digits.index(str[0])
        str = str[1:]

    if str and str[0] == '.':
        str = str[1:]
        dotvalue = 0
        dotdigits = 0
        while str and str[0] in digits:
            dotvalue = (dotvalue * base) + digits.index(str[0])
            dotdigits += 1
            str = str[1:]
        
        value += dotvalue / (base ** dotdigits)
    
    assert not str
    if neg:
        value = -value

    return to_fixnum(value)

k_char_escapes = {
    '*': '\1', '#': '\2', '-': '\3', '|': '\4', '+': '\5', '^': '\6',
    'a': '\a', 'b': '\b', 't': '\t', 'n': '\n', 'v': '\v', 'f': '\f', 'r': '\r',
    '\\': '\\', '"': '"', "'": "'", '\n': '\n',
}

def parse_string_literal(str):
    if str.startswith("["):
        start = str.index("[", 1) + 1
        return str[start:-start]

    else:
        litparts = []
        str = str[1:-1]
        start = 0
        while start < len(str):
            end = str.find('\\', start)
            if end < 0:
                litparts.append(str[start:])
                break

            if end > start:
                litparts.append(str[start:end])

            esc = str_get(str, end + 1)
            esc_ch = k_char_escapes.get(esc)
            if esc_ch:
                start = end + 2
                litparts.append(esc_ch)

            elif esc == 'z':
                start = end + 2
                while str_get(str, start) in k_wspace:
                    start += 1

            elif esc == 'x':
                start = end + 4
                hex_esc = str[end + 2 : start]
                value = maybe_int(hex_esc, base=16)
                if value is None:
                    raise Exception("Invalid hex escape: %s" % hex_esc)
                litparts.append(chr(value))

            elif '0' <= esc <= '9':
                start = end + 2
                while start < end + 4 and '0' <= str_get(str, start, '') <= '9':
                    start += 1
                dec_esc = str[end + 1 : start]
                value = maybe_int(dec_esc)
                if value is None or value >= 256:
                    raise Exception("Invalid dec escape: %s" % dec_esc)
                litparts.append(chr(value))

            else:
                raise Exception("Invalid escape: %s" % esc)
                
        return "".join(litparts)

def lint_code(ctxt, tokens, root, lint_rules):
    errors = []
    vars = defaultdict(list)
    builtin_globals = ctxt.globals
    custom_globals = set()

    lint_undefined = lint_unused = lint_duplicate = True
    if isinstance(lint_rules, dict):
        lint_undefined = lint_rules.get("undefined", True)
        lint_unused = lint_rules.get("unused", True)
        lint_duplicate = lint_rules.get("duplicate", True)

    for token in tokens:
        if token.type == TokenType.lint:
            for value in token.value:
                custom_globals.add(value)

    def add_error(msg, node):
        err = Error(msg, node)
        errors.append(err)

    # find global assignment, and check for uses

    used_locals = set()
    assigned_locals = set()

    def is_assign_target(node):
        return node.parent.type == NodeType.assign and node in node.parent.targets
    def is_op_assign_target(node):
        return node.parent.type == NodeType.op_assign and node == node.parent.target
    def is_function_target(node):
        return node.parent.type == NodeType.function and node == node.parent.target

    def preprocess_vars(node):        
        if node.type == NodeType.var:
            if node.kind == VarKind.global_ and node.name not in custom_globals:
                assign = False
                if is_assign_target(node):
                    func = node.find_parent(NodeType.function)
                    assign = True
                elif is_function_target(node):
                    func = node.parent.find_parent(NodeType.function)
                    assign = True

                if assign and (func == None or func.kind == "_init" or (func.kind is None and func.name == "_init" and func.find_parent(NodeType.function) == None)):
                    custom_globals.add(node.name)
                    vars[node.name].append(node.var)

            if node.kind == VarKind.local and not node.new:
                if is_assign_target(node) or is_op_assign_target(node) or is_function_target(node):
                    assigned_locals.add(node.var)
                else:
                    used_locals.add(node.var)

    root.traverse_nodes(preprocess_vars)

    # check for issues

    def lint_pre(node):
        if node.type == NodeType.var:
            if node.kind == VarKind.local and node.new:
                if lint_duplicate and vars[node.name] and node.name not in ('_', '_ENV'):
                    prev_var = vars[node.name][-1]
                    if isinstance(prev_var, Global):
                        add_error("Local '%s' has the same name as a global" % node.name, node)
                    elif prev_var.scope.funcdepth < node.var.scope.funcdepth:
                        if prev_var.scope.funcdepth == 0:
                            add_error("Local '%s' has the same name as a local declared at the top level" % node.name, node)
                        else:
                            add_error("Local '%s' has the same name as a local declared in a parent function" % node.name, node)
                    elif prev_var.scope.depth < node.var.scope.depth:
                        add_error("Local '%s' has the same name as a local declared in a parent scope" % node.name, node)
                    else:
                        add_error("Local '%s' has the same name as a local declared in the same scope" % node.name, node)
                
                vars[node.name].append(node.var)

                if lint_unused and node.var not in used_locals and not node.name.startswith("_"):
                    if node.var in assigned_locals:
                        add_error("Local '%s' is only ever assigned to, never used" % node.name, node)
                    elif not (node.parent.type == NodeType.function and node in node.parent.params and node != node.parent.params[-1]):
                        add_error("Local '%s' isn't used" % node.name, node)

            elif node.kind == VarKind.global_:
                if lint_undefined and node.name not in custom_globals:
                    if node.name in builtin_globals:
                        if is_assign_target(node):
                            add_error("Built-in global '%s' assigned outside _init - did you mean to use 'local'?" % node.name, node)
                        elif is_function_target(node):
                            add_error("Built-in global '%s' assigned outside _init - did you mean to use 'local function'?" % node.name, node)
                    else:
                        if is_assign_target(node):
                            add_error("Identifier '%s' not found - did you mean to use 'local' to define it?" % node.name, node)
                        elif is_function_target(node):
                            add_error("Identifier '%s' not found - did you mean to use 'local function' to define it?" % node.name, node)
                        else:
                            add_error("Identifier '%s' not found" % node.name, node)

    def lint_post(node):
        for scope in node.end_scopes:
            for item in scope.items:
                vars[item].pop()

    root.traverse_nodes(lint_pre, lint_post, extra=True)
    return errors

def obfuscate_tokens(ctxt, root, rules_input):
    all_globals = ctxt.globals.copy()
    global_knowns = global_callbacks.copy()
    member_knowns = member_strings.copy()
    known_tables = set()
    preserve_members = False

    if isinstance(rules_input, dict):
        for key, value in rules_input.items():
            if value == False:
                if key == "*.*":
                    preserve_members = True
                elif key.endswith(".*"):
                    known_tables.add(key[:-2])
                elif key.startswith("*."):
                    member_knowns.add(key[2:])
                else:
                    global_knowns.add(key)
            elif value == True:
                if key == "*.*":
                    preserve_members = False
                elif key.endswith(".*"):
                    known_tables.discard(key[:-2])
                elif key.startswith("*."):
                    member_knowns.discard(key[2:])
                else:
                    all_globals.discard(key)
                    global_knowns.discard(key)
            else:
                fail(value)

    # collect char histogram

    char_uses = CounterDictionary()
    def collect_chars(token):
        if token.type != TokenType.ident and not token.fake:
            for ch in token.value:
                char_uses[ch] += 1

    root.traverse_tokens(collect_chars)

    k_identifier_chars = string.ascii_letters + string.digits + "_"
    
    ident_chars = []
    for ch in sorted(char_uses, key=lambda k: char_uses[k], reverse=True):
        if ch in k_identifier_chars:
            ident_chars.append(ch)
    
    for ch in k_identifier_chars:
        if ch not in ident_chars:
            ident_chars.append(ch)

    ident_char_order_map = {ch1: ch2 for ch1, ch2 in zip(ident_chars, ident_chars[1:])}

    # collect ident uses

    global_uses = CounterDictionary()
    member_uses = CounterDictionary()
    local_uses = CounterDictionary()
    scopes = []

    def compute_effective_kind(node, kind, explicit):
        if kind == VarKind.member:
            table_name = None
            
            if node.parent.type == NodeType.member and node.parent.key == node and node.parent.child.type == NodeType.var:
                var_node = node.parent.child
                table_name = var_node.name

                if not explicit and var_node.var and var_node.var.keys_kind != None:
                    return compute_effective_kind(node, var_node.var.keys_kind, explicit=True)

            elif not explicit and node.parent.type == NodeType.table_member and node.parent.key == node:
                table_node = node.parent.parent
                if table_node.keys_kind != None:
                    return compute_effective_kind(node, table_node.keys_kind, explicit=True)

                if table_node.parent.type in (NodeType.assign, NodeType.local) and table_node in table_node.parent.sources:
                    assign_i = table_node.parent.sources.index(table_node)
                    target_node = list_get(table_node.parent.targets, assign_i)
                    if target_node and target_node.type == NodeType.var and target_node.var and target_node.var.keys_kind != None:
                        return compute_effective_kind(node, target_node.var.keys_kind, explicit=True)
            
            if preserve_members:
                return None
            elif node.name in member_knowns:
                return None
            elif table_name in known_tables:
                return None
            elif table_name == "_ENV":
                return compute_effective_kind(node, VarKind.global_, explicit=True)

        elif kind == VarKind.global_:
            if not explicit:
                env_var = node.parent_scope.find("_ENV")
                if env_var and env_var.keys_kind != None:
                    return compute_effective_kind(node, env_var.keys_kind, explicit=True)

            if node.name in global_knowns:
                return None
            elif node.name in all_globals:
                global_knowns.add(node.name)
                return None

        elif kind == VarKind.local:
            if node.var.implicit:
                return None
            elif node.name == "_ENV": # e.g. new locals named it
                return None

        return kind

    def collect_idents_pre(node):
        scope = node.start_scope
        if e(scope):
            scope.used_globals = set()
            scope.used_locals = set()
            scopes.append(scope)
            
        if node.type == NodeType.var:
            node.effective_kind = compute_effective_kind(node, default(node.var_kind, node.kind), explicit=e(node.var_kind))
            
            if node.effective_kind == VarKind.member:
                member_uses[node.name] += 1

            elif node.effective_kind == VarKind.global_:
                global_uses[node.name] += 1
                for scope in scopes:
                    scope.used_globals.add(node.name)

            elif node.effective_kind == VarKind.local:
                # should in theory help, but doesn't...
                #if node.new:
                #    local_uses[node.var] = 0
                #else:
                local_uses[node.var] += 1

                if node.var.scope in scopes:
                    i = scopes.index(node.var.scope)
                    for scope in scopes[i:]:
                        scope.used_locals.add(node.var)

    def collect_idents_post(node):
        for scope in node.end_scopes:
            assert scopes.pop() == scope

    root.traverse_nodes(collect_idents_pre, collect_idents_post, extra=True)

    # assign idents

    def get_next_ident_char(ch, first):
        nextch = ident_char_order_map.get(ch) if ch else ident_chars[0]
        while first and nextch and (nextch.isdigit() or nextch == '_'): # note: we avoid leading underscores too
            nextch = ident_char_order_map.get(nextch)
        if nextch:
            return nextch, True
        else:
            return ident_chars[0], False

    def create_ident_stream():
        next_ident = ""

        def get_next_ident():
            nonlocal next_ident
            for i in range(len(next_ident)-1, -1, -1):
                next_ch, found = get_next_ident_char(next_ident[i], i==0)
                next_ident = str_replace_at(next_ident, i, 1, next_ch)
                if found:
                    break
            else:
                next_ident = str_insert(next_ident, 0, get_next_ident_char(None, True)[0])
            return next_ident

        return get_next_ident

    def assign_idents(uses, excludes, skip=0):
        ident_stream = create_ident_stream()
        rename_map = {}

        for i in range(skip):
            ident_stream()

        for value in sorted(uses, key=lambda k: uses[k], reverse=True):
            while True:
                ident = ident_stream()
                if ident not in excludes and ident not in keywords:
                    break

            rename_map[value] = ident

        return rename_map

    member_renames = assign_idents(member_uses, member_knowns)
    global_renames = assign_idents(global_uses, global_knowns)
    rev_global_renames = {v: k for k, v in global_renames.items()}
    
    local_ident_stream = create_ident_stream()
    local_renames = {}

    remaining_local_uses = list(sorted(local_uses, key=lambda k: local_uses[k], reverse=True))
    while remaining_local_uses:
        ident = local_ident_stream()
        ident_global = rev_global_renames.get(ident, ident)
        ident_locals = []
        
        for i, var in enumerate(remaining_local_uses):
            if ident_global in var.scope.used_globals or ident_global in var.scope.used_locals:
                continue
            
            for _, ident_local in ident_locals:
                if ident_local in var.scope.used_locals:
                    break
                if var in ident_local.scope.used_locals:
                    break

            else:
                local_renames[var] = ident
                ident_locals.append((i, var))

        for i, ident_local in reversed(ident_locals):
            assert remaining_local_uses.pop(i) == ident_local

    # output

    def update_srcmap(mapping, kind):
        for old, new in mapping.items():
            old_name = old.name if isinstance(old, Local) else old

            ctxt.srcmap.append("%s %s <- %s" % (kind, from_pico_chars(new), old_name))

    if e(ctxt.srcmap):
        update_srcmap(member_renames, "member")
        update_srcmap(global_renames, "global")
        update_srcmap(local_renames, "local")

    def update_idents(node):
        if node.type == NodeType.var:
            orig_name = node.name

            if node.effective_kind == VarKind.member:
                node.name = member_renames[node.name]
            elif node.effective_kind == VarKind.global_:
                node.name = global_renames[node.name]
            elif node.effective_kind == VarKind.local:
                node.name = local_renames[node.var]
            else:
                return

            if node.parent.type == NodeType.const: # const string interpreted as identifier case
                assert len(node.parent.children) == 1 and node.parent.extra_names[node.extra_i] == orig_name
                node.parent.extra_names[node.extra_i] = node.name
                node.parent.children[0].value = '"%s"' % ",".join(node.parent.extra_names)
            else:
                assert len(node.children) == 1 and node.children[0].value == orig_name
                node.children[0].value = node.name
            
    root.traverse_nodes(update_idents, extra=True)

def from_fixnum(value):
    neg = value & 0x80000000
    if neg:
        value = (-value) & 0xffffffff
    if value & 0xffff:
        value /= (1 << 16)
    else:
        value >>= 16
    return -value if neg else value

# essentially only returns decvalue right now, given mostly non-fract. inputs
# TODO: test with fract-ish inputs to see what's best to do.
def format_fixnum(value, minus=False):
    intvalue = value >> 16
    dotvalue = value & 0xffff

    hexvalue = "0x%x" % intvalue
    if dotvalue:
        hexvalue = "0x" if hexvalue == "0x0" else hexvalue
        hexvalue += (".%04x" % dotvalue).rstrip('0')
        
    def str_add_1(str):
        if not str:
            return "1"
        elif str[-1] == ".":
            return str_add_1(str[:-1]) + "."
        elif str[-1] == "9":
            return str_add_1(str[:-1]) + "0"
        else:
            return str[:-1] + chr(ord(str[-1]) + 1)
    
    numvalue = value / (1 << 16)
    decvalue = "%.10f" % numvalue
    while "." in decvalue:
        nextvalue = decvalue[:-1]
        nextupvalue = str_add_1(nextvalue)
        if parse_fixnum(nextvalue) == value:
            decvalue = nextvalue
        elif parse_fixnum(nextupvalue) == value:
            decvalue = nextupvalue
        else:
            break
    if decvalue.startswith("0."):
        decvalue = decvalue[1:]

    minvalue = hexvalue if len(hexvalue) < len(decvalue) else decvalue

    if value & 0x80000000 and value != 0x80000000:
        negvalue = "-" + format_fixnum(-value & 0xffffffff)
        if len(negvalue) < len(minvalue):
            minvalue = negvalue

    return minvalue

k_char_escapes_rev = {v: k for k, v in k_char_escapes.items() if k not in ('\n', "'")}
k_char_escapes_rev.update({"\0": "0", "\x0e": "14", "\x0f": "15"})

def format_string_literal(value):
    litparts = []
    for i, ch in enumerate(value):
        if ch in k_char_escapes_rev:
            esc = k_char_escapes_rev[ch]
            if esc.isdigit() and i + 1 < len(value) and value[i + 1].isdigit():
                esc = esc.rjust(3, '0')
            litparts.append("\\" + esc)
        else:
            litparts.append(ch)
    return '"%s"' % "".join(litparts)

def get_precedence(node):
    if node.type == NodeType.binary_op:
        return k_binary_op_precs[node.op]
    elif node.type == NodeType.unary_op:
        return k_unary_ops_prec

def is_right_assoc(node):
    if node.type == NodeType.binary_op:
        return node.op in k_right_binary_ops
    else:
        return False

def is_vararg_expr(node):
    return node.type in (NodeType.call, NodeType.varargs)
    
def minify_code(source, tokens, root, minify):

    minify_lines = minify_wspace = minify_tokens = minify_comments = True
    if isinstance(minify, dict):
        minify_lines = minify.get("lines", True)
        minify_wspace = minify.get("wspace", True)
        minify_tokens = minify.get("tokens", True)
        minify_comments = minify.get("comments", True)

    vlines = defaultdict(set)

    def remove_parens(token):
        token.value = None
        end_token = token.parent.children[-1]
        assert end_token.value == ")"
        end_token.value = None

    def fixup_tokens(token):
        # update vline data

        if token.value in ("if", "then", "while", "do", "?"):
            vlines[token.vline].add(token.value)

        if minify_tokens:
            
            # remove unneeded tokens

            if token.value == ";" and token.parent.type == NodeType.block and token.next_token().value != "(":
                if not (getattr(token.parent.parent, "short", False) and not token.parent.stmts):
                    token.value = None
                    return

            if token.value in (",", ";") and token.parent.type == NodeType.table and token.next_sibling().value == "}":
                token.value = None
                return

            if token.value == "(" and token.parent.type == NodeType.call and len(token.parent.args) == 1:
                arg = token.parent.args[0]
                if arg.type == NodeType.table or (arg.type == NodeType.const and arg.token.type == TokenType.string):
                    return remove_parens(token)

            if token.value == "(" and token.parent.type == NodeType.group:
                inner, outer = token.parent.child, token.parent.parent
                inner_prec, outer_prec = get_precedence(inner), get_precedence(outer)
                if e(inner_prec) and e(outer_prec) and (inner_prec > outer_prec or (inner_prec == outer_prec and
                        (outer_prec == k_unary_ops_prec or is_right_assoc(outer) == (outer.right == token.parent)))):
                    return remove_parens(token)
                if outer.type in (NodeType.group, NodeType.table_index, NodeType.table_member, NodeType.op_assign):
                    return remove_parens(token)
                if outer.type in (NodeType.call, NodeType.print) and (token.parent in outer.args[:-1] or 
                        (outer.args and token.parent == outer.args[-1] and not is_vararg_expr(inner))):
                    return remove_parens(token)
                if outer.type in (NodeType.assign, NodeType.local, NodeType.for_in) and (token.parent in outer.sources[:-1] or 
                        (outer.sources and token.parent == outer.sources[-1] and (not is_vararg_expr(inner) or len(outer.targets) <= len(outer.sources)))):
                    return remove_parens(token)
                if outer.type == NodeType.return_ and (token.parent in outer.rets[:-1] or 
                        (outer.rets and token.parent == outer.rets[-1] and not is_vararg_expr(inner))):
                    return remove_parens(token)
                if outer.type in (NodeType.if_, NodeType.elseif, NodeType.while_, NodeType.until) and not getattr(outer, "short", False):
                    return remove_parens(token)

            # replace tokens for higher consistency

            if token.value == ";" and token.parent.type == NodeType.table:
                token.value = ","

            if token.value == "!=":
                token.value = "~="

            if token.type == TokenType.string and token.value.startswith("'") and '"' not in token.value:
                token.value = '"' + token.value[1:-1] + '"'

            if token.type == TokenType.number:
                token.value = format_fixnum(parse_fixnum(token.value))

    root.traverse_tokens(fixup_tokens)

    output = []

    if minify_wspace:
        # add keep: comments (for simplicity, at start)
        for token in tokens:
            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)

        def has_shorthands(vline):
            data = vlines[vline]
            return ("if" in data and "then" not in data) or ("while" in data and "do" not in data) or ("?" in data)

        prev_token = Token.dummy(None)
        def output_tokens(token):
            nonlocal prev_token
            if token.value is None:
                return

            if prev_token.endidx < token.idx and prev_token.value:

                # note: always adding \n before if/while wins a few bytes on my code (though similar tactics for other keywords and spaces don't work?)
                if prev_token.vline != token.vline and (not minify_lines or has_shorthands(prev_token.vline) or has_shorthands(token.vline)):
                    output.append("\n")
                    
                else:
                    combined = prev_token.value + token.value
                    ct, ce = tokenize(PicoSource(None, combined))
                    if ce or len(ct) != 2 or (ct[0].type, ct[0].value, ct[1].type, ct[1].value) != (prev_token.type, prev_token.value, token.type, token.value):
                        output.append(" ")

            output.append(token.value)
            prev_token = token

        root.traverse_tokens(output_tokens)

    else:
        # just remove the comments (if needed), with minimal impact on visible whitespace
        prev_token = Token.dummy(None)

        def output_wspace(wspace):
            if minify_comments:
                i = 0
                pre_i, post_i = 0, 0
                while True:
                    next_i = wspace.find("--", i)
                    if next_i < 0:
                        post_i = i
                        break
                    
                    if pre_i == 0:
                        pre_i = next_i

                    # TODO: --[[]]/etc comments...
                    i = wspace.find("\n", next_i)
                    i = i if i >= 0 else len(wspace)

                result = wspace[:pre_i] + wspace[post_i:]
                if post_i > 0 and not result:
                    result = " "
                output.append(result)
            else:
                output.append(wspace)

        for token in tokens:
            if token.type == TokenType.lint:
                continue

            output_wspace(source.text[prev_token.endidx:token.idx])

            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)
            elif token.value != None:
                output.append(token.value)
                
            prev_token = token

        output_wspace(source.text[prev_token.endidx:])

    return "".join(output)

def print_token_count(num_tokens, prefix=""):
    print_size(prefix + "tokens:", num_tokens, 8192)

def process_code(ctxt, source, count=False, lint=False, minify=False, obfuscate=False, fail=True):
    need_count = count not in (None, False)
    need_lint = lint not in (None, False)
    need_minify = minify not in (None, False)
    need_obfuscate = obfuscate not in (None, False)

    ok = False
    tokens, errors = tokenize(source)
    if not errors and (need_lint or need_minify):
        root, errors = parse(source, tokens)
        
    if not errors:
        ok = True
        if need_count:
            num_tokens = count_tokens(tokens)
            print_token_count(num_tokens)

        if need_lint:
            errors = lint_code(ctxt, tokens, root, lint)
        
        if need_minify:
            if need_obfuscate:
                obfuscate_tokens(ctxt, root, obfuscate)

            source.text = minify_code(source, tokens, root, minify)

    if fail and errors:
        raise Exception("\n".join(map(str, errors)))
    return ok, errors

def echo_code(code, echo):
    code = from_pico_chars(code)
    if echo == True:
        for line in code.splitlines():
            print(line)
    else:
        file_write_text(echo, code)
        
