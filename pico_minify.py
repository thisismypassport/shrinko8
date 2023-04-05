from utils import *
from pico_tokenize import TokenType, tokenize, Token, k_char_escapes
from pico_tokenize import parse_string_literal, parse_fixnum
from pico_parse import NodeType
from pico_parse import k_unary_ops_prec, k_binary_op_precs, k_right_binary_ops

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
def format_fixnum(value, allow_minus=False):
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

def format_string_literal(value, use_ctrl_chars=True, long=False):
    # currently, I'm unable to find a better-than-nothing heuristic for long strings's compression size
    # if len(strlit) > len(value) + len(long_prefix) + 4 and ...
    if long and "\0" not in value and "\r" not in value and "]]" not in value:
        long_prefix = "\n" if value.startswith("\n") else ""
        # note: we never generate [=[]=] and the like, as pico doesn't like it much
        return "[[%s%s]]" % (long_prefix, value)

    char_escapes_rev = k_char_escapes_rev_min if use_ctrl_chars else k_char_escapes_rev
    if value.count('"') <= value.count("'"):
        opener = closer = '"'
        exclude_esc = "'"
    else:
        opener = closer = "'"
        exclude_esc = '"'

    litparts = []
    for i, ch in enumerate(value):
        if ch in char_escapes_rev and ch != exclude_esc:
            esc = char_escapes_rev[ch]
            if esc.isdigit() and i + 1 < len(value) and value[i + 1].isdigit():
                esc = esc.rjust(3, '0')
            litparts.append("\\" + esc)
        else:
            litparts.append(ch)

    return '%s%s%s' % (opener, "".join(litparts), closer)

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
            token.value = format_string_literal(sublang.minify(), long=token.value.startswith('['))

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
             
            #TODO: enable this in a few weeks. (but re-verify it helps first?)
            #if token.value == "^^":
            #    token.value = "~"

            if token.type == TokenType.string:
                token.value = format_string_literal(parse_string_literal(token.value), long=token.value.startswith('['))

            if token.type == TokenType.number:
                outer_prec = get_precedence(token.parent.parent) if token.parent.type == NodeType.const else None
                allow_minus = outer_prec is None or outer_prec < k_unary_ops_prec
                token.value = format_fixnum(parse_fixnum(token.value), allow_minus=allow_minus)
                if token.value.startswith("-"):
                    # insert synthetic minus token, so that output_tokens's tokenize won't get confused
                    token.value = token.value[1:]
                    minus_token = Token.synthetic(TokenType.punct, "-", token, prepend=True)
                    token.parent.children.insert(0, minus_token)
                    tokens.insert(tokens.index(token), minus_token)

    root.traverse_tokens(fixup_tokens)

    output = []

    def need_whitespace_between(prev_token, token):
        combined = prev_token.value + token.value
        ct, ce = tokenize(PicoSource(None, combined))
        return ce or len(ct) != 2 or (ct[0].type, ct[0].value, ct[1].type, ct[1].value) != (prev_token.type, prev_token.value, token.type, token.value)

    def need_linebreak_between(prev_token, token):
        # TODO: starting from 0.2.5d we could probably be more adventurous with shorthands... (except '?')
        return prev_token.vline != token.vline and (not minify_lines or prev_token.vline in shorthand_vlines or token.vline in shorthand_vlines)

    if minify_wspace:
        # add keep: comments (for simplicity, at start)
        for token in tokens:
            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)

        prev_token = Token.dummy(None)
        def output_tokens(token):
            nonlocal prev_token
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
        # just remove the comments (if needed), with minimal impact on visible whitespace
        prev_token = Token.dummy(None)
        prev_welded_token = None

        def output_wspace(wspace):
            if minify_comments and not wspace.isspace():
                start_i, end_i = 0, len(wspace)

                while start_i < len(wspace) and wspace[start_i].isspace():
                    start_i += 1

                while end_i > 0 and wspace[end_i - 1].isspace():
                    end_i -= 1

                result = wspace[:start_i] + wspace[end_i:]
                if wspace and not result:
                    result = " "
                output.append(result)
            else:
                output.append(wspace)

        for token in tokens:
            if token.type == TokenType.lint:
                continue

            if prev_token.endidx != token.idx:
                output_wspace(source.text[prev_token.endidx:token.idx])
                prev_welded_token = None
            
            # extra whitespace may be needed due to modified or deleted tokens
            if prev_welded_token and token.value and (prev_welded_token.modified or token.modified or prev_welded_token != prev_token):
                if need_whitespace_between(prev_welded_token, token):
                    output.append(" ")

            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)
            elif token.value != None:
                output.append(token.value)
                prev_welded_token = token
                
            prev_token = token

        output_wspace(source.text[prev_token.endidx:])

    return "".join(output), tokens

from pico_process import PicoSource
