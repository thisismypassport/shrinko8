from utils import *
from pico_defs import to_pico_chars, from_pico_chars

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
    "unpack", "yield",
}

deprecated_globals = {
    "band", "bnot", "bor", "bxor",
    "lshr", "rotl", "rotr", "shl", "shr",
    "mapdraw", 
}

undocumented_globals = {
    "holdframe", "_set_fps", "_update_buttons",
    "_map_display", "_get_menu_item_selected", "_ENV",
}

short_globals = {
    "t",
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

class PicoSource:
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
    def __init__(m, name, text, mappings):
        super().__init__(name, text)
        m.mappings = mappings

    def get_name_line_col(m, idx):
        name, line, col = super().get_name_line_col(idx)

        real_name, real_line = name, line
        for mapping in m.mappings:
            if line >= mapping.line:
                real_name = mapping.name
                real_line = line - mapping.line + mapping.real_line
        
        return real_name, real_line, col

class VarKind(Enum):
    values = ("local", "global_", "member")
    
class Local:
    def __init__(m, name, scope, implicit):
        m.name, m.scope, m.implicit = name, scope, implicit

class Scope:
    def __init__(m, parent=None, depth=0):
        m.parent = parent
        m.depth = depth
        m.items = {}

    def add(m, var):
        m.items[var.name] = var

    def find(m, item):
        if item in m.items:
            return m.items[item]
        elif m.parent:
            return m.parent.find(item)

class PicoContext:
    def __init__(m, deprecated=False, undocumented=True, short=False, patterns=True, srcmap=None, extra_globals=set()):
        funcs = set(main_globals)
        if deprecated:
            funcs |= deprecated_globals
        if undocumented:
            funcs |= undocumented_globals
        if short:
            funcs |= short_globals
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

def read_code(filename, defines=None, pp_handler=None):
    lines = []
    defines = defines.copy() if defines else {}
    ppstack = []
    ppline = None
    active = True
    mappings = []

    def get_active():
        return ppstack[-1] if ppstack else True

    def get_defined(m):
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
            raise Exception("Undefined: %s" % key)

    def get_conditional(m):
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
                raise Exception("Invalid preprocessor line: %s" % line)

            mappings.append(Dynamic(line=len(lines), name=name, real_line=i + 1))

        elif active:
            line = define_cond_re.sub(get_conditional, line)
            line = define_use_re.sub(get_defined, line) # put this regex last (handles escape)

            lines.append(to_pico_chars(line))

    def add_code_file(name):
        data = file_read_text(path_join(root_dir, name))
        file_lines = data.splitlines(keepends=True)
        i = 0
        if list_get(file_lines, i).startswith("pico-8 cartridge"):
            i += 1
        if list_get(file_lines, i).startswith("__lua__"):
            i += 1
            
        mappings.append(Dynamic(line=len(lines), name=name, real_line=i))

        for line in file_lines[i:]:
            add_code_line(name, i, line)
            i += 1
    
    root_dir = path_dirname(filename)
    add_code_file(path_basename(filename))

    text = "".join(lines)
    return PicoComplexSource(path_basename(filename), text, mappings)

k_lint_prefix = "lint:"
k_keep_prefix = "keep:"
k_nameof_global_comment = "nameof"
k_nameof_member_comment = "memberof"

k_wspace = " \t\r\n"

def is_ident_char(ch):
    return '0' <= ch <= '9' or 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch == '_' or ch >= chr(0x80)

def tokenize(source):
    text = source.text
    idx = 0
    vline = 0
    tokens = []
    errors = []
    next_nameof = None

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

    def add_error(msg, off=-1):
        errors.append(Error(msg, Token.dummy(source, idx + off)))

    def tokenize_line_comment():
        nonlocal vline
        orig_idx = idx
        while take() not in ('\n', ''): pass
        vline += 1

        comment = text[orig_idx:idx]
        if comment.startswith(k_lint_prefix):
            add_token(TokenType.lint, orig_idx, value=[v.strip() for v in comment[len(k_lint_prefix):].split(",")])
        elif comment.startswith(k_keep_prefix):
            add_token(TokenType.comment, orig_idx, value=comment[len(k_keep_prefix):].rstrip())

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
        nonlocal idx, next_nameof
        ok, orig_idx, start, end = tokenize_long_brackets(0)
        if ok:
            comment = text[start:end]
            if comment == k_nameof_global_comment:
                next_nameof = VarKind.global_
            elif comment == k_nameof_member_comment:
                next_nameof = VarKind.member
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
        nonlocal idx, next_nameof
        orig_idx = idx + off
        idx = orig_idx + 1
        quote = text[orig_idx]

        while True:
            ch = take()
            if ch in ('\n', ''):
                add_error("Unterminated_string")
                break
            elif ch == '\\':
                take() # at least
                if accept('z'): # skip line breaks
                    while peek() in k_wspace:
                        take()
            elif ch == quote:
                break

        add_token(TokenType.string, orig_idx)
        if next_nameof:
            tokens[-1].nameof = next_nameof
            next_nameof = None

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
            if token.type == TokenType.lint and "count::stop" in token.value:
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
              "for_", "for_in", "return_", "break_", "goto", "label", "print", "block", "do",
              # ext-only:
              "explicit_varargs")

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

def parse(source, tokens, exts=False):
    idx = 0
    scope = None
    depth = -1
    errors = []

    tokens = [t for t in tokens if not t.fake]
   
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

        return Node(NodeType.var, [token], name=name, kind=kind, var=var, new=bool(newscope))
    
    def parse_function(stmt=False, local=False):
        nonlocal scope
        tokens = [peek(-1)]
        
        target, name = None, None
        funcscope = Scope(scope, depth + 1)
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

        scope = funcscope
        body = parse_block()
        tokens.append(body)
        require("end", tokens)
        scope = scope.parent

        return Node(NodeType.function, tokens, target=target, params=params, body=body, name=name, scopespec=funcscope)

    def parse_table():
        tokens = [peek(-1)]
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

        return Node(NodeType.table, tokens, items=items)

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

    def parse_nameof(node):
        token = node.token
        if hasattr(token, "nameof"):
            node.extra_names = token.value[1:-1].split(",")
            node.extra_children = [Node(NodeType.var, [], name=value, kind=token.nameof, var=None, new=False, parent=node, extra_i=i) 
                                   for i, value in enumerate(node.extra_names)]
        return node

    def parse_core_expr():
        token = peek()
        value = take().value
        if value == None:
            add_error("unexpected end of input", fail=True)
        elif value in ("nil", "true", "false") or token.type in (TokenType.number, TokenType.string):
            return parse_nameof(Node(NodeType.const, [token], token=token))
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
            elif value == "..." and exts:
                return Node(NodeType.explicit_varargs, [expr, token], child=expr)
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
            newscope = Scope(scope, depth + 1)
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
            newscope = Scope(scope, depth + 1)
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
        newscope = Scope(scope, depth)

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
        if peek().type != None:
            add_error("Expected end of input")
        assert scope is None
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

def lint_code(ctxt, tokens, root):
    errors = []
    vars = CounterDictionary()
    allowed_globals = ctxt.globals.copy()

    for token in tokens:
        if token.type == TokenType.lint:
            for value in token.value:
                allowed_globals.add(value)

    def add_error(msg, node):
        err = Error(msg, node)
        errors.append(err)

    # find global assignment, and check for uses

    used_locals = set()

    def preprocess_vars(node):        
        if node.type == NodeType.var:
            if node.kind == VarKind.global_ and node.name not in allowed_globals:
                assign = False
                if node.parent.type == NodeType.assign and node in node.parent.targets:
                    func = node.find_parent(NodeType.function)
                    assign = True
                elif node.parent.type == NodeType.function and node == node.parent.target:
                    func = node.parent.find_parent(NodeType.function)
                    assign = True

                if assign and (func == None or (func.name == "_init" and func.find_parent(NodeType.function) == None)):
                    allowed_globals.add(node.name)

            if node.kind == VarKind.local and not node.new and node.var not in used_locals:
                used_locals.add(node.var)

    root.traverse_nodes(preprocess_vars)

    # check for issues

    def lint_pre(node):
        if node.type == NodeType.var:
            if node.kind == VarKind.local and node.new:
                if vars[node.name] > 0 and node.name not in ('_', '_ENV'):
                    add_error("Identifier %s already defined" % node.name, node)
                vars[node.name] += 1

                if node.var not in used_locals and node.name not in ('_', '_ENV'):
                    if not (node.parent.type == NodeType.function and node in node.parent.params and node != node.parent.params[-1]):
                        add_error("identifier %s isn't used" % node.name, node)

            elif node.kind == VarKind.global_:
                if node.name not in allowed_globals:
                    add_error("Identifier %s not found" % node.name, node)

    def lint_post(node):
        for scope in node.end_scopes:
            for item in scope.items:
                vars[item] -= 1

    root.traverse_nodes(lint_pre, lint_post, extra=True)
    return errors

def obfuscate_tokens(ctxt, root, rules_input):
    global_knowns = global_callbacks.copy()
    member_knowns = member_strings.copy()
    known_tables = set()

    if isinstance(rules_input, dict):
        for key, value in rules_input.items():
            assert value == False
            if key.endswith(".*"):
                known_tables.add(key[:-2])
            elif key.startswith("*."):
                member_knowns.add(key[2:])
            else:
                global_knowns.add(key)

    # collect ident uses

    global_uses = CounterDictionary() # also contains "global locals"
    member_uses = CounterDictionary()
    local_uses = CounterDictionary() # non-global locals only
    scopes = []

    def collect_idents_pre(node):
        scope = node.start_scope
        if e(scope):
            scope.used_globals = set()
            scope.used_locals = set()
            scopes.append(scope)
            
        if node.type == NodeType.var:
            node.effective_kind = node.kind

            while True:
                if node.effective_kind == VarKind.member:
                    table_name = None
                    if node.parent.type == NodeType.member and node.parent.child.type == NodeType.var:
                        table_name = node.parent.child.name
                    
                    if node.name in member_knowns:
                        node.effective_kind = None
                    elif table_name in known_tables:
                        node.effective_kind = None
                    elif table_name == "_ENV":
                        node.effective_kind = VarKind.global_
                        continue

                elif node.effective_kind == VarKind.global_:
                    if node.name == "_ENV":
                        node.effective_kind = None
                    elif node.name in global_knowns:
                        node.effective_kind = None
                    elif node.name in ctxt.globals:
                        global_knowns.add(node.name)
                        node.effective_kind = None

                elif node.effective_kind == VarKind.local:
                    if node.name == "_ENV":
                        node.effective_kind = None
                    elif node.var.implicit:
                        node.effective_kind = None

                break
            
            if node.effective_kind == VarKind.member:
                member_uses[node.name] += 1
            elif node.effective_kind == VarKind.global_:
                global_uses[node.name] += 1
                for scope in scopes:
                    scope.used_globals.add(node.name)

            elif node.effective_kind == VarKind.local:
                if False: # glocals don't work well
                    global_uses[node.var] += 1
                else:
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
        if ch == None: return 'a', True
        elif ch == 'z': return 'A' if first else '0', True # note: we avoid leading underscores
        elif ch == '9': return '_', True
        elif ch == '_': return 'A', True
        elif ch == 'Z': return get_next_ident_char(None, first)[0], False
        else: return chr(ord(ch) + 1), True

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

    def assign_idents(uses, excludes):
        ident_stream = create_ident_stream()
        rename_map = {}

        for value in sorted(uses, key=lambda k: uses[k], reverse=True):
            while True:
                ident = ident_stream()
                if ident not in excludes:
                    break

            rename_map[value] = ident

        return rename_map

    member_renames = assign_idents(member_uses, member_knowns)
    global_renames = assign_idents(global_uses, global_knowns)  # also contains "global locals"
    rev_global_renames = {v: k for k, v in global_renames.items()}
    
    local_ident_stream = create_ident_stream()
    local_renames = {} # non-global locals only

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

    def update_srcmap(mapping, kind, local_kind):
        for old, new in mapping.items():
            old_name = old.name if isinstance(old, Local) else old
            this_kind = local_kind if isinstance(old, Local) else kind

            ctxt.srcmap.append("%s %s <- %s" % (this_kind, from_pico_chars(new), old_name))

    if e(ctxt.srcmap):
        update_srcmap(member_renames, "member", None)
        update_srcmap(global_renames, "global", "glocal")
        update_srcmap(local_renames, None, "local")

    def update_idents(node):
        if node.type == NodeType.var:
            orig_name = node.name

            if node.effective_kind == VarKind.member:
                node.name = member_renames[node.name]
            elif node.effective_kind == VarKind.global_:
                node.name = global_renames[node.name]
            elif node.effective_kind == VarKind.local:
                if False: # glocals don't work well
                    node.name = global_renames[node.var]
                else:
                    node.name = local_renames[node.var]
            else:
                return

            if node.parent.type == NodeType.const: # nameof/memberof case
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

def minify_code(source, tokens, root, minify):
    vlines = defaultdict(set)

    minify_lines = True
    minify_wspace = True
    if isinstance(minify, dict):
        minify_lines = minify.get("lines")
        minify_wspace = minify.get("wspace")

    output = []

    if minify_wspace:
        def fixup_tokens(token):
            nonlocal prev_token

            # update vline data

            if token.value in ("if", "then", "while", "do", "?"):
                vlines[token.vline].add(token.value)

            # remove unneeded tokens

            if token.value == ";" and token.parent.type == NodeType.block and token.next_token().value != "(" and \
               (token.parent.stmts or not getattr(token.parent.parent, "short", False)):
                token.value = None
                return

            if token.value in (",", ";") and token.parent.type == NodeType.table and token.next_sibling().value == "}":
                token.value = None
                return

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

        prev_token = Token.dummy(None)

        # add keep: comments (for simplicity, at start)
        for token in tokens:
            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)

        def has_shorthands(vline):
            data = vlines[vline]
            return ("if" in data and "then" not in data) or ("while" in data and "do" not in data) or ("?" in data)

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
        # just remove the comments, with minimal impact on visible whitespace
        prev_token = Token.dummy(None)

        def output_wspace(wspace):
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

        for token in tokens:
            if token.type == TokenType.lint:
                continue

            output_wspace(source.text[prev_token.endidx:token.idx])

            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)
            else:
                output.append(source.text[token.idx:token.endidx])
                
            prev_token = token

        output_wspace(source.text[prev_token.endidx:])

    return "".join(output)

def process_code(ctxt, source, count=False, lint=False, minify=False, obfuscate=False, fail=True):
    tokens, errors = tokenize(source)
    if not errors and (lint or minify):
        root, errors = parse(source, tokens)
        
    if not errors:
        if count:
            num_tokens = count_tokens(tokens)
            print("tokens:", num_tokens, str(int(num_tokens / 8192 * 100)) + "%")

        if lint:
            errors = lint_code(ctxt, tokens, root)
        
        if minify:
            if obfuscate:
                obfuscate_tokens(ctxt, root, obfuscate)

            source.new_text = minify_code(source, tokens, root, minify)

    if fail and errors:
        raise Exception("\n".join(map(str, errors)))
    return errors

def echo_code(code, echo):  
    if echo == True:
        for line in code.splitlines():
            print(line)
    else:
        file_write_text(echo, code)
        
