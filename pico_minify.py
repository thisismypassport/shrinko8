from utils import *
from pico_tokenize import TokenType, tokenize, Token, k_char_escapes, CommentHint
from pico_tokenize import parse_string_literal, parse_fixnum, k_keep_prefix
from pico_parse import NodeType
from pico_parse import k_unary_ops_prec, k_binary_op_precs, k_right_binary_ops

# essentially only returns decvalue right now, given mostly non-fract. inputs
# TODO: test with fract-ish inputs to see what's best to do.
def format_fixnum(value, allow_minus=False):
    """format a fixnum to a pico8 string"""
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

    if allow_minus and value & 0x80000000 and value != 0x80000000:
        negvalue = "-" + format_fixnum(-value & 0xffffffff)
        if len(negvalue) < len(minvalue):
            minvalue = negvalue

    return minvalue

k_char_escapes_rev = {v: k for k, v in k_char_escapes.items() if k != '\n'}
k_char_escapes_rev.update({"\0": "0", "\x0e": "14", "\x0f": "15"})

k_char_escapes_rev_min = {k: v for k, v in k_char_escapes_rev.items() if k in "\0\n\r\"'\\"}

def format_string_literal(value, use_ctrl_chars=True, long=None, quote=None):
    """format a pico8 string to a pico8 string literal"""

    if long != False:
        if "\0" not in value and "\r" not in value and "]]" not in value:
            long_prefix = "\n" if value.startswith("\n") else ""
            # note: we never generate [=[]=] and the like, as pico doesn't like it much
            strlong = "[[%s%s]]" % (long_prefix, value)
            if long == True:
                return strlong
        else:
            strlong = None
            long = False

    if long != True:
        if quote is None:
            quote = '"' if value.count('"') <= value.count("'") else "'"

        exclude_esc = "'" if quote == '"' else '"'
            
        char_escapes_rev = k_char_escapes_rev_min if use_ctrl_chars else k_char_escapes_rev

        litparts = []
        for i, ch in enumerate(value):
            if ch in char_escapes_rev and ch != exclude_esc:
                esc = char_escapes_rev[ch]
                if esc.isdigit() and i + 1 < len(value) and value[i + 1].isdigit():
                    esc = esc.rjust(3, '0')
                litparts.append("\\" + esc)
            else:
                litparts.append(ch)

        strlit = '%s%s%s' % (quote, "".join(litparts), quote)
        if long == False:
            return strlit

    return strlong if len(strlong) < len(strlit) else strlit

def minify_string_literal(token, focus_chars, value=None):
    if value is None:
        value = parse_string_literal(token.value)
    
    if focus_chars:
        return format_string_literal(value)
    else:
        # haven't found a good balanced heuristic for 'long' yet
        return format_string_literal(value, long=token.value.startswith('['))

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

def minify_needs_comments(minify):
    # returns whether minify_code makes use of the tokens' comments
    return isinstance(minify, dict) and not minify.get("wspace", True)
    
def minify_code(source, ctxt, root, minify):

    minify_lines = minify_wspace = minify_tokens = minify_comments = True
    focus_chars = focus_compressed = False
    if isinstance(minify, dict):
        minify_lines = minify.get("lines", True)
        minify_wspace = minify.get("wspace", True)
        minify_tokens = minify.get("tokens", True)
        minify_comments = minify.get("comments", True)
        focus_chars = minify.get("focus") == "chars"
        focus_compressed = minify.get("focus") == "compressed"

    shorthand_vlines = set()

    def remove_parens(token):
        token.value = None
        end_token = token.parent.children[-1]
        assert end_token.value == ")"
        end_token.value = None

    def fixup_tokens(token):
        # find shorthands

        if token.value == "?" or (token.value in ("if", "while") and getattr(token.parent, "short", False)):
            shorthand_vlines.add(token.vline)
    
        # minify sublangs

        sublang = getattr(token, "sublang", None)
        if sublang and sublang.minify:
            token.value = minify_string_literal(token, focus_chars, value=sublang.minify())

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
                if outer.type in (NodeType.group, NodeType.table_member, NodeType.table_index, NodeType.op_assign):
                    return remove_parens(token)
                if outer.type in (NodeType.call, NodeType.print) and (token.parent in outer.args[:-1] or 
                        (outer.args and token.parent == outer.args[-1] and not is_vararg_expr(inner))):
                    return remove_parens(token)
                if outer.type in (NodeType.assign, NodeType.local) and (token.parent in outer.sources[:-1] or 
                        (outer.sources and token.parent == outer.sources[-1] and (not is_vararg_expr(inner) or len(outer.targets) <= len(outer.sources)))):
                    return remove_parens(token)
                if outer.type in (NodeType.return_, NodeType.table) and (token.parent in outer.items[:-1] or
                        (outer.items and token.parent == outer.items[-1] and not is_vararg_expr(inner))):
                    return remove_parens(token)
                if outer.type in (NodeType.if_, NodeType.elseif, NodeType.while_, NodeType.until) and not getattr(outer, "short", False):
                    return remove_parens(token)

            # replace tokens for higher consistency

            if token.value == ";" and token.parent.type == NodeType.table:
                token.value = ","

            if token.value == "!=":
                token.value = "~="
             
            if token.value == "^^" and ctxt.version >= 37:
                token.value = "~"

            if token.type == TokenType.string:
                token.value = minify_string_literal(token, focus_chars)

            if token.type == TokenType.number:
                outer_prec = get_precedence(token.parent.parent) if token.parent.type == NodeType.const else None
                allow_minus = outer_prec is None or outer_prec < k_unary_ops_prec
                token.value = format_fixnum(parse_fixnum(token.value), allow_minus=allow_minus)
                if token.value.startswith("-"):
                    # insert synthetic minus token, so that output_tokens's tokenize won't get confused
                    token.value = token.value[1:]
                    minus_token = Token.synthetic(TokenType.punct, "-", token, prepend=True)
                    token.parent.children.insert(0, minus_token)

    root.traverse_tokens(fixup_tokens)

    output = []

    def need_whitespace_between(prev_token, token):
        combined = prev_token.value + token.value
        ct, ce = tokenize(PicoSource(None, combined))
        return ce or len(ct) != 2 or (ct[0].type, ct[0].value, ct[1].type, ct[1].value) != (prev_token.type, prev_token.value, token.type, token.value)

    def need_linebreak_between(prev_token, token):
        return e(prev_token.vline) and e(token.vline) and prev_token.vline != token.vline and \
            (not minify_lines or prev_token.vline in shorthand_vlines)

    if minify_wspace:
        # output the tokens as tightly as possible
        prev_token = Token.none
        def output_tokens(token):
            nonlocal prev_token

            if token.children:
                for comment in token.children:
                    if comment.hint == CommentHint.keep:
                        output.append(comment.value.replace(k_keep_prefix, "", 1))

            if token.value is None:
                return

            # (modified tokens may require whitespace not previously required - e.g. 0b/0x)
            if (prev_token.endidx < token.idx or prev_token.modified or token.modified) and prev_token.value:
                # TODO: always adding \n before if/while won a few bytes on my code - check if this is consistent & helpful.

                if need_linebreak_between(prev_token, token):
                    output.append("\n")                    
                elif need_whitespace_between(prev_token, token):
                    output.append(" ")

            output.append(token.value)
            prev_token = token

        root.traverse_tokens(output_tokens)

    else:
        # output both tokens and surrounding whitespace, possible excluding comments
        prev_token = Token.none
        prev_welded_token = None

        def output_tokens(token):
            nonlocal prev_token, prev_welded_token
            if prev_token.endidx != token.idx:
                wspace = source.text[prev_token.endidx:token.idx]
                if minify_comments and token.children:
                    # only output spacing before and after the comments between the tokens
                    prespace = source.text[prev_token.endidx:token.children[0].idx]
                    postspace = source.text[token.children[-1].endidx:token.idx]
                    output.append(prespace)
                    if "\n" in wspace and "\n" not in prespace and "\n" not in postspace:
                        output.append("\n")
                    elif wspace and not prespace and not postspace:
                        output.append(" ")
                    output.append(postspace)
                else:
                    output.append(wspace)
                prev_welded_token = None
            
            # extra whitespace may be needed due to modified or deleted tokens
            if prev_welded_token and token.value and (prev_welded_token.modified or token.modified or prev_welded_token != prev_token):
                if need_whitespace_between(prev_welded_token, token):
                    output.append(" ")

            if token.value != None:
                output.append(token.value)
                prev_welded_token = token
                
            prev_token = token
        
        root.traverse_tokens(output_tokens)

    return "".join(output)

from pico_process import PicoSource
