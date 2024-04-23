from utils import *
from pico_tokenize import tokenize, parse_fixnum
from pico_tokenize import Token, k_char_escapes, CommentHint, k_keep_prefix
from pico_parse import k_nested

# essentially only returns decvalue right now, given mostly non-fract. inputs
# TODO: test with fract-ish inputs to see what's best to do.
def format_fixnum(value, sign=None, base=None):
    """format a fixnum to a pico8 string"""
    if sign:
        if sign == '-':
            value = -value & 0xffffffff
        elif sign == '~':
            value = ~value & 0xffffffff
        else:
            throw("invalid sign")

    intvalue = value >> 16
    dotvalue = value & 0xffff

    if base is None or base == 16:
        hexvalue = "0x%x" % intvalue
        if dotvalue:
            hexvalue = "0x" if hexvalue == "0x0" else hexvalue
            hexvalue += (".%04x" % dotvalue).rstrip('0')
        
        if base:
            minvalue = hexvalue
        
    if base is None or base == 10:
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
        decvalue = "%.6f" % numvalue
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
            
        if base:
            minvalue = decvalue

    if not base:
        minvalue = hexvalue if len(hexvalue) < len(decvalue) else decvalue

    if sign:
        minvalue = sign + minvalue
    
    if sign is None and value & 0x80000000 and value != 0x80000000:
        negvalue = format_fixnum(value, sign='-', base=base)
        if len(negvalue) < len(minvalue):
            minvalue = negvalue
            
        notvalue = format_fixnum(value, sign='~', base=base)
        if len(notvalue) < len(minvalue):
            minvalue = notvalue

    return minvalue

k_char_escapes_rev = {v: k for k, v in k_char_escapes.items() if k != '\n'}
k_char_escapes_rev.update({"\0": "0", "\x0e": "14", "\x0f": "15"})

k_char_escapes_rev_min = {k: v for k, v in k_char_escapes_rev.items() if k in "\0\n\r\"'\\"}

def format_string_literal(value, use_ctrl_chars=True, use_complex_long=True, long=None, quote=None):
    """format a pico8 string to a pico8 string literal"""

    if long != False:
        if "\0" not in value and "\r" not in value and (use_complex_long or "]]" not in value):
            newline = "\n" if value.startswith("\n") else ""

            for i in itertools.count():
                eqs = "=" * i
                if f"]{eqs}]" not in value:
                    break
            
            strlong = f"[{eqs}[{newline}{value}]{eqs}]"
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

def need_whitespace_between(prev_token, token):
    combined = prev_token.value + token.value
    ct, ce = tokenize(Source(None, combined))
    return ce or len(ct) != 2 or (ct[0].type, ct[0].value, ct[1].type, ct[1].value) != (prev_token.type, prev_token.value, token.type, token.value)

def need_newline_after(node):
    # (k_nested is set for shorthands used in the middle of a line - we don't *YET* generate this ourselves (TODO: do for 0.2.6b+), but we do preserve it)
    return node.short and node.short is not k_nested

def output_min_wspace(root, minify_lines=True):
    """convert a root back to a string, inserting as little whitespace as possible"""
    output = []
    prev_token = Token.none
    prev_vline = 0
    need_linebreak = False

    def output_tokens(token):
        nonlocal prev_token, prev_vline, need_linebreak

        if token.children:
            for comment in token.children:
                if comment.hint == CommentHint.keep:
                    output.append(comment.value.replace(k_keep_prefix, "", 1))

        if token.value is None:
            return

        # (modified tokens may require whitespace not previously required - e.g. 0b/0x)
        if (prev_token.endidx < token.idx or prev_token.modified or token.modified) and prev_token.value:
            # TODO: can we systemtically add whitespace to imrpove compression? (failed so far)

            if need_linebreak or (not minify_lines and e(token.vline) and token.vline != prev_vline):
                output.append("\n")
                need_linebreak = False
            elif need_whitespace_between(prev_token, token):
                output.append(" ")

        output.append(token.value)
        prev_token = token
        if e(token.vline):
            prev_vline = token.vline

    def post_node_output(node):
        nonlocal need_linebreak
        if need_newline_after(node):
            need_linebreak = True
    
    root.traverse_nodes(tokens=output_tokens, post=post_node_output)
    return "".join(output)

def output_original_wspace(root, exclude_comments=False):
    """convert a root back to a string, using original whitespace (optionally except comments)"""
    output = []
    prev_token = Token.none
    prev_vline = 0
    need_linebreak = False

    def get_wspace(pre, post, allow_linebreaks, need_linebreak=False):
        source = default(pre.source, post.source)
        text = source.text[pre.endidx:post.idx]
        
        if not text.isspace():
            # verify this range contains only whitespace/comments (may contain more due to reorders/removes)
            tokens, _ = tokenize(Source(None, text))
            if tokens:
                if "\n" in text and allow_linebreaks:
                    need_linebreak = True
                text = text[:tokens[0].idx] or text[tokens[-1].endidx:]

        if not allow_linebreaks and "\n" in text:
            text = text[:text.index("\n")] + " "
        if need_linebreak and "\n" not in text:
            text += "\n"

        return text

    def output_tokens(token):
        nonlocal prev_token, prev_vline, need_linebreak
        
        if token.value is None:
            return
        
        if prev_token.endidx != token.idx or prev_token.modified or token.modified:
            allow_linebreaks = e(token.vline) and token.vline != prev_vline
            wspace = get_wspace(prev_token, token, allow_linebreaks, need_linebreak)

            if not wspace and prev_token.value != None and need_whitespace_between(prev_token, token):
                wspace += " "

            if exclude_comments and token.children:
                # only output spacing before and after the comments between the tokens
                prespace = get_wspace(prev_token, token.children[0], allow_linebreaks)
                postspace = get_wspace(token.children[-1], token, allow_linebreaks)
                for comment in token.children:
                    if comment.hint == CommentHint.keep:
                        prespace += comment.value.replace(k_keep_prefix, "", 1)
                
                output.append(prespace)
                if "\n" in wspace and "\n" not in prespace and "\n" not in postspace:
                    output.append("\n")
                elif wspace and not prespace and not postspace:
                    output.append(" ")
                output.append(postspace)
            else:
                output.append(wspace)
            
            need_linebreak = False
        
        output.append(token.value)            
        prev_token = token
        if e(token.vline):
            prev_vline = token.vline
    
    def post_node_output(node):
        nonlocal need_linebreak
        if need_newline_after(node):
            need_linebreak = True
    
    root.traverse_nodes(tokens=output_tokens, post=post_node_output)
    return "".join(output)

from pico_process import Source
