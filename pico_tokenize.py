from utils import *
from pico_cart import k_long_brackets_re, k_wspace, PicoPreprocessor

keywords = {
    "and", "break", "do", "else", "elseif", "end", "false", 
    "for", "function", "goto", "if", "in", "local", "nil", 
    "not", "or", "repeat", "return", "then", "true", "until",
    "while"
}

k_lint_prefix = "lint:"
k_keep_prefix = "keep:"

k_lint_func_prefix = "func::"
k_lint_count_stop = "count::stop"

k_language_prefix = "language::"

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
        if parent is None:
            return None
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

    def add_extra_child(m, child):
        if not hasattr(m, "extra_children"):
            m.extra_children = []
        child.parent = m
        child.extra_i = len(m.extra_children)
        m.extra_children.append(child)

class TokenType(Enum):
    values = ("number", "string", "ident", "keyword", "punct", "comment", "lint")

class Token(TokenNodeBase):
    def __init__(m, type, value, source=None, idx=None, endidx=None, vline=None):
        super().__init__()
        m.type, m.value, m.source, m.idx, m.endidx, m.vline, m.modified = type, value, source, idx, endidx, vline, False

    @classmethod
    def dummy(m, source, idx=None):
        if idx is None:
            idx = len(source.text) if source else 0
        return Token(None, None, source, idx, idx, 0)

    @classmethod
    def synthetic(m, type, value, other, append=False, prepend=False):
        idx = other.endidx if append else other.idx
        endidx = other.idx if prepend else other.endidx
        return Token(type, value, other.source, idx, endidx, 0)

    @property
    def fake(m):
        return m.type in (TokenType.lint, TokenType.comment)

class CustomPreprocessor(PicoPreprocessor):
    def __init__(m, defines=None, pp_handler=None, **kwargs):
        super().__init__(**kwargs)
        m.defines = defines.copy() if defines else {}
        m.pp_handler = pp_handler
        m.ppstack = []
        m.active = True
        
    def get_active(m):
        return m.ppstack[-1] if m.ppstack else True
        
    def start(m, path, code):
        pass

    def handle(m, path, code, i, start_i, out_i, outparts, outmappings):
        end_i = code.find("\n", i)
        while end_i >= 0 and code[end_i - 1] == '\\':
            end_i = code.find("\n", end_i + 1)

        end_i = end_i if end_i >= 0 else len(code)
        line = code[i:end_i].replace("\\\n", "")
        args = line.split()
        
        op = args[0] if args else ""

        if op == "#include" and len(args) == 2:
            if m.active:
                out_i = m.read_included_cart(path, args[1], out_i, outparts, outmappings)

        elif op == "#define" and len(args) >= 2:
            if m.active:
                value = line.split(maxsplit=2)[2].rstrip() if len(args) > 2 else ""
                m.defines[args[1]] = value

        elif op == "#undef" and len(args) == 2:
            if m.active:
                del m.defines[args[1]]

        elif op == "#ifdef" and len(args) == 2:
            m.active &= args[1] in m.defines
            m.ppstack.append(m.active)

        elif op == "#ifndef" and len(args) == 2:
            m.active &= args[1] not in m.defines
            m.ppstack.append(m.active)

        elif op == "#else" and len(args) == 1 and m.ppstack:
            old_active = m.ppstack.pop()
            m.active = m.get_active() and not old_active
            m.ppstack.append(m.active)

        elif op == "#endif" and len(args) == 1 and m.ppstack:
            m.ppstack.pop()
            m.active = m.get_active()

        elif not (m.pp_handler and m.pp_handler(op=op, args=args, ppline=line, active=m.active, outparts=outparts)):
            raise Exception("Invalid preprocessor line: %s" % line)

        # (do not keep empty lines, unlike PicoPreprocessor)
        return m.active, end_i + 1, end_i + 1, out_i
        
    def handle_inline(m, path, code, i, start_i, out_i, outparts, outmappings):
        if not m.active:
            return False, i + 1, start_i, out_i

        orig_i = i
        i += 2
        negate = False
        if list_get(code, i) == '!':
            i += 1
            negate = True
        key_i = i
        while is_ident_char(list_get(code, i, '')):
            i += 1
        key = code[key_i:i]
        op = code[orig_i:i + 1]

        if list_get(code, i) == ']' and not negate:
            end_i = i + 1

            value = m.pp_handler(op=op, args=(), ppline=op, active=True, outparts=outparts) if m.pp_handler else None
            if value is None:
                if key in m.defines:
                    value = m.defines[key]
                else:
                    raise Exception("Undefined preprocessor variable: %s" % key)

        elif list_get(code, i) == '[':
            cond_args = []
            while list_get(code, i) == '[':
                match = k_long_brackets_re.match(code, i)
                if not match:
                    raise Exception("Unterminated preprocessor long brackets")

                i = match.end()
                inline = code[orig_i:i + 1]
                cond_args.append(match.group(2))

            if list_get(code, i) == ']':
                end_i = i + 1
            else:
                raise Exception("Invalid inline preprocesor directive: %s" % inline)

            value = m.pp_handler(op=op, args=cond_args, ppline=inline, active=True, outparts=outparts) if m.pp_handler else None
            if value is None:
                if len(cond_args) > 2:
                    raise Exception("Too many inline preprocessor directive params: %s" % inline)
                if (key in m.defines) ^ negate:
                    value = list_get(cond_args, 0, "")
                else:
                    value = list_get(cond_args, 1, "")
        else:
            raise Exception("Invalid inline preprocesor directive: %s" % op)

        outparts.append(value)
        return True, end_i, end_i, out_i + len(value)

    def finish(m, path, code):
        if m.ppstack:
            raise Exception("Unterminated preprocessor ifs")
    
def is_ident_char(ch):
    return '0' <= ch <= '9' or 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch == '_' or ch >= chr(0x80)

def is_identifier(str):
    return str and all(is_ident_char(ch) for ch in str) and not str[:1].isdigit() and str not in keywords
    
k_identifier_split_re = re.compile(r"([0-9A-Za-z_\x80-\xff]+)")

def tokenize(source, ctxt=None):
    text = source.text
    idx = 0
    vline = 0
    tokens = []
    errors = []
    next_var_kind = None
    next_keys_kind = None
    next_func_kind = None
    next_sublang = None

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

    def add_sublang(token, sublang_name):
        if ctxt and ctxt.sublang_getter and token.type == TokenType.string:
            sublang_cls = ctxt.sublang_getter(sublang_name)
            if sublang_cls:
                add_lang_error = lambda msg: add_error("%s: %s" % (sublang_name, msg))
                tokens[-1].sublang_name = sublang_name
                tokens[-1].sublang = sublang_cls(parse_string_literal(token.value), on_error=add_lang_error)
                return

    def add_token_kinds():
        nonlocal next_var_kind, next_keys_kind, next_func_kind, next_sublang
        if next_var_kind != None:
            tokens[-1].var_kind = next_var_kind
            next_var_kind = None
        if next_keys_kind != None:
            tokens[-1].keys_kind = next_keys_kind
            next_keys_kind = None
        if next_func_kind != None:
            tokens[-1].func_kind = next_func_kind
            next_func_kind = None
        if next_sublang != None:
            add_sublang(tokens[-1], next_sublang)
            next_sublang = None

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
            nonlocal next_var_kind, next_keys_kind, next_sublang
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
            elif comment.startswith(k_language_prefix) and not any(ch.isspace() for ch in comment):
                next_sublang = comment[len(k_language_prefix):]

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
                add_error("Unterminated string", orig_idx - idx)
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

        elif '0' <= ch <= '9' or (ch == '.' and '0' <= peek() <= '9'): # number
            tokenize_number(-1)

        elif is_ident_char(ch): # identifier
            tokenize_ident(-1)

        elif ch in ('"', "'"): # string
            tokenize_string(-1)

        elif ch == '[' and accept_one_of('=', '['): # long string
            tokenize_long_string(-2)

        elif ch == '-' and accept('-'): # comment
            if not tokenize_long_comment():
                tokenize_line_comment()

        elif ch == '/' and accept('/'): # c-style comment
            tokenize_line_comment()

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

        if token.value in (",", ".", ":", ";", "::", ")", "]", "}", "end", "local", None):
            continue

        if token.value in ("-", "~") and i+1 < len(tokens) and tokens[i+1].type == TokenType.number and \
            i-1 >= 0 and tokens[i-1].type not in (TokenType.number, TokenType.string, TokenType.ident) and \
            tokens[i-1].value not in (")", "]", "}", ";", "end"):
            continue

        count += 1
    return count

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
        end = -start
        if str[start] == '\n':
            start += 1
        return str[start:end]

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

from pico_parse import Node, VarKind
from pico_process import Error
