from utils import *
from pico_preprocess import k_wspace
from pico_defs import num_to_fixnum

keywords = {
    "and", "break", "do", "else", "elseif", "end", "false", 
    "for", "function", "goto", "if", "in", "local", "nil", 
    "not", "or", "repeat", "return", "then", "true", "until",
    "while"
}

k_preserve_prefix = "preserve:"
k_lint_prefix = "lint:"
k_keep_prefix = "keep:"

k_lint_func_prefix = "func::"
k_lint_count_stop = "count::stop"

k_language_prefix = "language::"
k_rename_prefix = "rename::"

class StopTraverse(BaseException):
    pass

k_skip_children = True # value returnable from traverse's pre-function

class TokenNodeBase:
    """Baseclass for both pico8 Tokens and pico8 Nodes.
    The syntax tree is comprised of these and can be traversed via traverse_nodes or traverse_tokens"""

    def __init__(m):
        m.parent, m.children = None, ()

    def __str__(m):
        return repr(m.__dict__)
    
    @property
    def source_text(m):
        if m.source and m.idx != None and m.endidx != None:
            return m.source.text[m.idx:m.endidx]
        else:
            return None
    
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

    def _find_token(m, delta, adjacent=False):
        i = 0 if delta > 0 else -1
        if adjacent:
            m = m._adjacent(delta)
        while isinstance(m, Node):
            if m.children:
                m = m.children[i]
            else:
                m = m._adjacent(delta)
        return m if m else Token.none

    def next_token(m): return m._find_token(1, adjacent=True)
    def prev_token(m): return m._find_token(-1, adjacent=True)

    def first_token(m): return m._find_token(1)
    def last_token(m): return m._find_token(-1)

    def traverse_nodes(m, pre=None, post=None, tokens=None, extra=False):
        skip = pre(m) if pre else None
        if not skip:
            for child in m.children:
                if isinstance(child, Node):
                    child.traverse_nodes(pre, post, tokens, extra)
                elif tokens:
                    tokens(child)
            if extra and hasattr(m, "extra_children"):
                for child in m.extra_children:
                    child.traverse_nodes(pre, post, tokens, extra)
        if post: post(m)

    def traverse_tokens(m, visit):
        for child in m.children:
            if isinstance(child, Node):
                child.traverse_tokens(visit)
            else:
                visit(child)
    
    def traverse_parents(m, visit):
        parent = m.parent
        while parent:
            visit(parent)
            parent = parent.parent

    def add_extra_child(m, child):
        if not hasattr(m, "extra_children"):
            m.extra_children = []
        child.parent = m
        child.extra_i = len(m.extra_children)
        m.extra_children.append(child)
    
    def is_extra_child(m):
        return hasattr(m, "extra_i")
    
    def move(m): # create a "destructive" copy - old object is no longer usable unless replaced
        cpy = copy(m)
        for child in cpy.children:
            child.parent = cpy
        m.erase()
        return cpy

    def copy(m):
        cpy = copy(m)
        cpy.children = [child.copy() for child in m.children]
        for child in cpy.children:
            child.parent = cpy
        for key, val in cpy.__dict__.items():
            idx = list_find(m.children, val)
            if idx >= 0:
                cpy.__dict__[key] = cpy.children[idx]
        return cpy

class TokenType(Enum):
    number = string = ident = keyword = punct = ...

class Token(TokenNodeBase):
    """A pico8 token, at 'source'.text['idx':'endidx'] (which is equal to its 'value'). Its 'type' is a TokenType.
    For string tokens, the actual string is 'string_value'
    For number tokens, the actual fixnum value is 'fixnum_value'
    Its children are the comments *before* it, if any."""

    def __init__(m, type, value, source, idx, endidx, vline=None, modified=False):
        super().__init__()
        m.type, m.value, m.source, m.idx, m.endidx, m.vline, m.modified = type, value, source, idx, endidx, vline, modified
    
    def check(m, expected):
        if isinstance(expected, tuple):
            assert m.value in expected
        else:
            assert m.value == expected

    def modify(m, value, expected=None):
        if expected != None:
            m.check(expected)
        m.value = value
        m.modified = True
        lazy_property.clear(m, "fixnum_value")
        lazy_property.clear(m, "string_value")
    
    def erase(m, expected=None):
        if expected != None:
            m.check(expected)
        m.type, m.value, m.modified = None, None, True

    @lazy_property
    def fixnum_value(m):
        return parse_fixnum(m.value)
    
    @lazy_property
    def string_value(m):
        return parse_string_literal(m.value)

    @classmethod
    def dummy(cls, source, idx=None, vline=None):
        if idx is None:
            idx = len(source.text) if source else 0
            vline = sys.maxsize if source else 0
        return cls(None, None, source, idx, idx, vline)

    # note: vline is kept only for initial parsing and is not to be relied upon

    @classmethod
    def synthetic(cls, type, value, other, append=False, prepend=False):
        idx = other.endidx if append else other.idx
        endidx = other.idx if prepend else other.endidx
        return cls(type, value, other.source, idx, endidx, modified=True)

Token.none = Token.dummy(None)

class ConstToken(Token):
    def __init__(m, type, other, fixnum_value=None, string_value=None, value=None):
        super().__init__(type, value, other.source, other.idx, other.endidx, modified=True)
        m.fixnum_value = fixnum_value
        m.string_value = string_value
        if value is None:
            lazy_property.clear(m, "value")

    @lazy_property
    def value(m): # used during going over chars for rename (tsk...) and for output when not minify-tokens
                  # (but not used for output under minify-tokens)
        if e(m.fixnum_value):
            allow_unary = can_replace_with_unary(m.parent)
            return format_fixnum(m.fixnum_value, sign=None if allow_unary else "")
        else:
            return format_string_literal(m.string_value, long=False)

class CommentHint(Enum):
    none = preserve = lint = keep = ...

class Comment(TokenNodeBase):
    """A pico8 comment, optionally holding some kind of hint"""

    def __init__(m, hint, hintdata=None, source=None, idx=None, endidx=None):
        super().__init__()
        m.hint, m.hintdata, m.source, m.idx, m.endidx = hint, hintdata, source, idx, endidx

    @property
    def value(m):
        return m.source_text

def is_ident_char(ch):
    return '0' <= ch <= '9' or 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch in ('_', '\x1e', '\x1f') or ch >= '\x80'

def is_identifier(str):
    return str and all(is_ident_char(ch) for ch in str) and not str[:1].isdigit() and str not in keywords
    
k_identifier_split_re = re.compile(r"([0-9A-Za-z_\x1e\x1f\x80-\xff]+)")

k_hint_split_re = re.compile(r"[\s,]+")

class NextTokenMods:
    def __init__(m):
        m.var_kind = m.keys_kind = m.is_const = m.func_kind = m.merge_prev = m.sublang = m.rename = None
        m.comments = None
        
    def add_comment(m, cmt):
        if m.comments is None:
            m.comments = []
        m.comments.append(cmt)

def tokenize(source, ctxt=None, all_comments=False):
    text = source.text
    idx = 0
    vline = 0
    tokens = []
    errors = []
    next_mods = None
    process_hints = ctxt and ctxt.hint_comments

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

    def get_next_mods():
        nonlocal next_mods
        if next_mods is None:
            next_mods = NextTokenMods()
        return next_mods

    def add_token(type, start, end_off=0, value=None):
        end = idx + end_off
        if value is None and type is not None: # (dummy tokens have type==value==None)
            value = text[start:end]
        token = Token(type, value, source, start, end, vline)
        tokens.append(token)
        
        nonlocal next_mods
        if next_mods != None:
            add_next_mods(token, next_mods)
            next_mods = None

    def add_error(msg, off=-1):
        add_token(None, idx + off) # error token
        errors.append(Error(msg, tokens[-1]))

    def add_sublang(token, sublang_name):
        if ctxt and ctxt.sublang_getter and token.type == TokenType.string:
            sublang_cls = ctxt.sublang_getter(sublang_name)
            if sublang_cls:
                add_lang_error = lambda msg: add_error(f"{sublang_name}: {msg}")
                token.sublang_name = sublang_name
                token.sublang = sublang_cls(parse_string_literal(token.value), on_error=add_lang_error)
                return

    def add_next_mods(token, mods):
        if mods.comments != None:
            token.children = mods.comments        
        if mods.var_kind != None:
            token.var_kind = mods.var_kind
        if mods.keys_kind != None:
            token.keys_kind = mods.keys_kind
        if mods.is_const != None:
            token.is_const = mods.is_const
        if mods.func_kind != None:
            token.func_kind = mods.func_kind
        if mods.merge_prev != None:
            token.merge_prev = mods.merge_prev
        if mods.rename != None:
            token.rename = mods.rename
        if mods.sublang != None:
            add_sublang(token, mods.sublang)

    def process_comment(orig_idx, comment, isblock):
        hint, hintdata = CommentHint.none, None

        if process_hints:
            if comment.startswith(k_lint_prefix):
                lints = k_hint_split_re.split(comment[len(k_lint_prefix):])
                hint, hintdata = CommentHint.lint, lints

                for lint in lints:
                    if lint.startswith(k_lint_func_prefix):
                        get_next_mods().func_kind = lint[len(k_lint_func_prefix):]

            elif comment.startswith(k_preserve_prefix):
                preserves = k_hint_split_re.split(comment[len(k_preserve_prefix):])
                hint, hintdata = CommentHint.preserve, preserves

            elif comment.startswith(k_keep_prefix):
                hint = CommentHint.keep

            elif isblock:
                if comment in ("global", "nameof"): # nameof is deprecated
                    get_next_mods().var_kind = VarKind.global_
                elif comment in ("member", "memberof"): # memberof is deprecated
                    get_next_mods().var_kind = VarKind.member
                elif comment in ("preserve", "string"): # string is deprecated
                    get_next_mods().var_kind = False
                elif comment == "global-keys":
                    get_next_mods().keys_kind = VarKind.global_
                elif comment == "member-keys":
                    get_next_mods().keys_kind = VarKind.member
                elif comment in ("preserve-keys", "string-keys"): # string-keys is deprecated
                    get_next_mods().keys_kind = False
                elif comment == "no-merge":
                    get_next_mods().merge_prev = False
                elif comment == "const":
                    get_next_mods().is_const = True
                elif comment == "non-const":
                    get_next_mods().is_const = False
                elif comment.startswith(k_language_prefix) and not any(ch.isspace() for ch in comment):
                    get_next_mods().sublang = comment[len(k_language_prefix):]
                elif comment.startswith(k_rename_prefix) and not any(ch.isspace() for ch in comment):
                    get_next_mods().rename = comment[len(k_rename_prefix):]
        
        if all_comments or hint != CommentHint.none:
            get_next_mods().add_comment(Comment(hint, hintdata, source, orig_idx, idx))

    def tokenize_line_comment():
        nonlocal vline
        orig_idx = idx
        while take() not in ('\n', ''): pass
        vline += 1

        process_comment(orig_idx - 2, text[orig_idx:idx], isblock=False)

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
                end_i = text.find(f"]{pad}]", idx)
                if end_i >= 0:
                    idx = end_i + len(pad) + 2
                    return True, orig_idx, start_i, end_i
                
                add_error("Unterminated long comment (no longer accepted by pico8)", 0)
        
        return False, orig_idx, None, None

    def tokenize_long_comment():
        nonlocal idx
        ok, orig_idx, start, end = tokenize_long_brackets(0)
        if ok:
            process_comment(orig_idx - 2, text[start:end], isblock=True)
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

        while True:
            ch = peek()
            if ch and ch in digits:
                idx += 1
            elif ch == '.':
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
    
    if next_mods or all_comments:
        add_token(None, idx) # end token, for ending whitespace/comments/etc
    return tokens, errors

def count_tokens(tokens):
    count = 0
    for i, token in enumerate(tokens):
        assert token.value != None

        if token.children:
            for comment in token.children:
                if comment.hint == CommentHint.lint and k_lint_count_stop in comment.hintdata:
                    return count

        if token.value in (",", ".", ":", ";", "::", ")", "]", "}", "end", "local"):
            continue

        if token.value in ("-", "~") and i+1 < len(tokens) and tokens[i+1].type == TokenType.number and \
            token.endidx == tokens[i+1].idx and \
            i-1 >= 0 and tokens[i-1].type not in (TokenType.number, TokenType.string, TokenType.ident) and \
            tokens[i-1].value not in (")", "]", "}", ";", "end"):
            continue

        count += 1
    return count

def parse_fixnum(origstr):
    """parse a fixnum from a pico8 string"""
    str = origstr.lower()
    neg = bnot = False
    if str.startswith("-"):
        str = str[1:]
        neg = True
    elif str.startswith("~"):
        str = str[1:]
        bnot = True

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
    
    if str:
        throw(f"Invalid number: {origstr}")
    if neg:
        value = -value
    elif bnot:
        value = ~value

    return num_to_fixnum(value)

k_char_escapes = {
    '*': '\1', '#': '\2', '-': '\3', '|': '\4', '+': '\5', '^': '\6',
    'a': '\a', 'b': '\b', 't': '\t', 'n': '\n', 'v': '\v', 'f': '\f', 'r': '\r',
    '\\': '\\', '"': '"', "'": "'", '\n': '\n',
}

def parse_string_literal(str):
    """parse a pico8 string from a pico8 string literal"""
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
                    throw(f"Invalid hex escape: {hex_esc}")
                litparts.append(chr(value))

            elif '0' <= esc <= '9':
                start = end + 2
                while start < end + 4 and '0' <= str_get(str, start, '') <= '9':
                    start += 1
                dec_esc = str[end + 1 : start]
                value = maybe_int(dec_esc)
                if value is None or value >= 256:
                    throw(f"Invalid dec escape: {dec_esc}")
                litparts.append(chr(value))

            else:
                throw(f"Invalid escape: {esc}")
                
        return "".join(litparts)

from pico_parse import Node, VarKind, can_replace_with_unary
from pico_output import format_fixnum, format_string_literal
from pico_process import Error
