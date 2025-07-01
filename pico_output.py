from utils import *
from pico_defs import k_fixnum_mask, k_luaint_mask, float_is_negative
from pico_tokenize import tokenize, parse_fixnum
from pico_tokenize import Token, k_char_escapes, CommentHint, k_keep_prefix
from pico_parse import k_nested

def float_str_add_1(str):
    if not str:
        return "1"
    elif str[-1] == ".":
        return float_str_add_1(str[:-1]) + "."
    elif str[-1] == "9":
        return float_str_add_1(str[:-1]) + "0"
    else:
        return str[:-1] + chr(ord(str[-1]) + 1)

def float_str_minify(str, parse, cmpval, keep_float=False):
    ok = parse(str) == cmpval

    while "." in str:
        ch = str[-1]
        if ch == '.':
            if not keep_float:
                str = str[:-1]
            break
        elif ch == "0" and ok: # easy case
            str = str[:-1]
            continue

        nextvalue = str[:-1]
        nextupvalue = float_str_add_1(nextvalue)
        if parse(nextvalue) == cmpval:
            str = nextvalue
            ok = True
        elif parse(nextupvalue) == cmpval:
            str = nextupvalue
            ok = True
        else:
            check(ok, "float_str_minify error")
            break
    
    if str.startswith("0.") and str != "0.":
        str = str[1:]
    return str

# essentially only returns decvalue right now, given mostly non-fract. inputs
# TODO: test with fract-ish inputs to see what's best to do.
def format_fixnum(value, sign=None, base=None):
    """format a fixnum to a pico8 string"""
    if sign:
        if sign == '-':
            value = -value & k_fixnum_mask
        elif sign == '~':
            value = ~value & k_fixnum_mask
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
        numvalue = value / (1 << 16)
        decvalue = float_str_minify("%.6f" % numvalue, parse_fixnum, value)
            
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

def float_sign(value):
    return "-" if float_is_negative(value) else ""

def float_hex(value, hexdigits, keep_float=False): # like value.hex(), except doesn't use an exponent
    hexval = hex(int(abs(value) * (1 << (hexdigits * 4))))[2:].rjust(hexdigits, '0')
    result = f"0x{hexval[:-hexdigits]}.{hexval[-hexdigits:]}".rstrip("0")
    if not keep_float:
        result = result.rstrip(".")
    if result in ("0x", "0x."):
        result = "0x0"
    return float_sign(value) + result

def format_luanum(value, sign=None, base=None):
    """format a luanum to a picotron string"""
    if isinstance(value, int):
        if sign:
            if sign == '-':
                value = -value
            elif sign == '~':
                value = ~value
            else:
                throw("invalid sign")
        
        value &= k_luaint_mask

        if base is None or base == 16:
            hexvalue = "0x%x" % value
            if base:
                minvalue = hexvalue
            
        if base is None or base == 10:
            decvalue = "%d" % value
            if base:
                minvalue = decvalue

        if not base:
            if value >= 0x8000000000000000:
                minvalue = hexvalue # else, it won't be parsed as an integer
            else:
                minvalue = hexvalue if len(hexvalue) < len(decvalue) else decvalue

        if sign:
            minvalue = sign + minvalue
        
        if sign is None and value & 0x8000000000000000 and value != 0x8000000000000000:
            negvalue = format_luanum(value, sign='-', base=base)
            if len(negvalue) < len(minvalue):
                minvalue = negvalue
                
            notvalue = format_luanum(value, sign='~', base=base)
            if len(notvalue) < len(minvalue):
                minvalue = notvalue

    else: # float
        parens = False
        if e(sign) and sign != float_sign(value):
            # only thing we can do is surround result in parens
            sign = None
            parens = True
            
        if sign is None:
            sign = float_sign(value)
        
        value = abs(value)
        
        if math.isinf(value):
            if base == 16:
                minvalue = "0x1p1111"
            else:
                minvalue = "1e333"

        elif math.isnan(value):
            raise ValueError("nan not supported") # could output <inf>*0 in parens? (0/0 doesn't currently nan)

        else:
            # TODO: this is very not optimal (but at least it's correct this time...)

            if base is None or base == 16:
                manvalue, expvalue = math.frexp(value)
                manvalue *= 2; expvalue -= 1 # the 1..2 range is better for us
                expvalue = f"{float_hex(manvalue, 56)}p{expvalue}"

                if value == 0 or 1e-4 <= value <= 1e24:
                    hexvalue = float_hex(value, 88, keep_float=True)
                    hexvalue = expvalue if len(expvalue) < len(hexvalue) else hexvalue
                else:
                    hexvalue = expvalue
                
                if base:
                    minvalue = hexvalue
                
            if base is None or base == 10:
                manstr, expstr = ("%.19e" % value).split("e")
                expstr = f"e{int(expstr)}"
                expvalue = float_str_minify(manstr, lambda v: float(v + expstr), value) + expstr

                if value == 0 or 1e-3 <= value <= 1e21:
                    decvalue = float_str_minify("%.24f" % value, float, value, keep_float=True)
                    decvalue = expvalue if len(expvalue) < len(decvalue) else decvalue
                else:
                    decvalue = expvalue
                
                if base:
                    minvalue = decvalue

            if not base:
                minvalue = hexvalue if len(hexvalue) < len(decvalue) else decvalue
        
        minvalue = sign + minvalue
        if parens:
            minvalue = "(" + minvalue + ")"

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

def need_whitespace_between(ctxt, prev_token, token):
    combined = prev_token.value + token.value
    ct, ce = tokenize(Source("<output>", combined), ctxt) # TODO: optimize?
    return ce or len(ct) != 2 or (ct[0].type, ct[0].value, ct[1].type, ct[1].value) != (prev_token.type, prev_token.value, token.type, token.value)

def is_non_nested_short(node):
    # k_nested is set for shorthands used in the middle of a line
    return node.short and node.short is not k_nested

def get_orig_wspace(pre, post, ctxt, allow_linebreaks, need_linebreak=False):
    source = default(pre.source, post.source)
    text = source.text[pre.endidx:post.idx]
    
    if not text.isspace():
        # verify this range contains only whitespace/comments (may contain more due to reorders/removes)
        tokens, _ = tokenize(Source("<output>", text), ctxt)
        if tokens:
            if "\n" in text and allow_linebreaks:
                need_linebreak = True
            text = text[:tokens[0].idx] or text[tokens[-1].endidx:]

    if not allow_linebreaks and "\n" in text:
        text = text[:text.index("\n")] + " "
    if need_linebreak and "\n" not in text:
        text += "\n"

    return text
    
def output_node(root, ctxt, minify_wspace=True, minify_lines=True, exclude_comments=True):
    """convert a root back to a string, inserting as little whitespace as possible (under minify_wspace),
       or using original whitespace (optionally except comments)"""
    output = []
    prev_token = Token.none
    prev_vline = 0
    need_linebreak = False
    short_level = 0

    def output_with_min_wspace(token):
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

            if need_linebreak or (not minify_lines and token.vline != prev_vline):
                output.append("\n")
                need_linebreak = False
            elif need_whitespace_between(ctxt, prev_token, token):
                output.append(" ")

        output.append(token.value)
        prev_token = token
        prev_vline = token.vline

    def output_with_orig_wspace(token):
        nonlocal prev_token, prev_vline, need_linebreak
        
        if token.value is None:
            return
        
        if prev_token.endidx != token.idx or prev_token.modified or token.modified:
            allow_linebreaks = token.vline != prev_vline
            wspace = get_orig_wspace(prev_token, token, ctxt, allow_linebreaks, need_linebreak)

            if not wspace and prev_token.value != None and need_whitespace_between(ctxt, prev_token, token):
                wspace += " "

            if exclude_comments and token.children:
                # only output spacing before and after the comments between the tokens
                prespace = get_orig_wspace(prev_token, token.children[0], ctxt, allow_linebreaks)
                postspace = get_orig_wspace(token.children[-1], token, ctxt, allow_linebreaks)
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
        prev_vline = token.vline
    
    def pre_node_output(node):
        nonlocal short_level
        if is_non_nested_short(node):
            short_level += 1

    def post_node_output(node):
        nonlocal short_level, need_linebreak
        if is_non_nested_short(node):
            short_level -= 1
            if short_level == 0:
                need_linebreak = True
    
    root.traverse_nodes(tokens=output_with_min_wspace if minify_wspace else output_with_orig_wspace,
                        pre=pre_node_output, post=post_node_output)
    return "".join(output)

def output_code(ctxt, root, minify_opts):
    minify_lines = minify_opts.get("lines", True)
    minify_wspace = minify_opts.get("wspace", True)
    minify_comments = minify_opts.get("comments", True)

    return output_node(root, ctxt, minify_wspace, minify_lines, minify_comments)

from pico_process import Source
