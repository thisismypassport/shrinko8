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

def float_str_minify(value, str, parse=float, keep_float=False):
    ok = parse(str) == value

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
        if parse(nextvalue) == value:
            str = nextvalue
            ok = True
        elif parse(nextupvalue) == value:
            str = nextupvalue
            ok = True
        else:
            #check(ok, "float_str_minify error") # can this happen? YES!
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
        decvalue = float_str_minify(value, "%.6f" % numvalue, parse_fixnum)
            
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

def float_hex(value, keep_float=False): # like value.hex(), except doesn't use an exponent
    precision = 56
    dotpos = precision // 4
    hexval = hex(int(abs(value) * (1 << precision)))[2:].rjust(dotpos, '0')
    result = f"0x{hexval[:-dotpos]}.{hexval[-dotpos:]}".rstrip("0")
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
        
        if math.isinf(value):
            if sign is None:
                sign = float_sign(value)

            if base == 16:
                minvalue = sign + "0x1p1111"
            else:
                minvalue = sign + "1e333"

        elif math.isnan(value):
            raise ValueError("nan not supported") # could output <inf>*0 in parens? (0/0 doesn't currently nan)

        else:
            few_digits = value == 0 or 1e-30 <= abs(value) <= 1e30 # to avoid needless computation (also avoids python denormal bug)
            
            if base is None or base == 16:
                manvalue, expvalue = math.frexp(value)
                manvalue *= 2; expvalue -= 1 # the 1..2 range is better for us
                expvalue = f"{float_hex(manvalue)}p{expvalue}"

                if few_digits:
                    hexvalue = float_hex(value, keep_float=True)
                    hexvalue = expvalue if len(expvalue) < len(hexvalue) else hexvalue
                else:
                    hexvalue = expvalue
                
                if base:
                    minvalue = hexvalue
                
            if base is None or base == 10:
                expvalue = int(math.log10(abs(value))) if value else 0
                manvalue = value / math.pow(10, expvalue)
                manvalue = float_str_minify(manvalue, "%.19f" % manvalue)
                expvalue = f"{manvalue}e{expvalue}"

                if few_digits:
                    decvalue = float_str_minify(value, "%.19f" % value, keep_float=True)
                    decvalue = expvalue if len(expvalue) < len(decvalue) else decvalue
                else:
                    decvalue = expvalue
                
                if base:
                    minvalue = decvalue

            if not base:
                minvalue = hexvalue if len(hexvalue) < len(decvalue) else decvalue
        
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

def need_newline_after(node):
    # (k_nested is set for shorthands used in the middle of a line - we don't *YET* generate this ourselves (TODO: do for 0.2.6b+), but we do preserve it)
    return node.short and node.short is not k_nested

def output_min_wspace(root, ctxt, minify_lines=True):
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
            elif need_whitespace_between(ctxt, prev_token, token):
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

def output_original_wspace(root, ctxt, exclude_comments=False):
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

    def output_tokens(token):
        nonlocal prev_token, prev_vline, need_linebreak
        
        if token.value is None:
            return
        
        if prev_token.endidx != token.idx or prev_token.modified or token.modified:
            allow_linebreaks = e(token.vline) and token.vline != prev_vline
            wspace = get_wspace(prev_token, token, allow_linebreaks, need_linebreak)

            if not wspace and prev_token.value != None and need_whitespace_between(ctxt, prev_token, token):
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

def output_code(ctxt, root, minify_opts):
    minify_lines = minify_opts.get("lines", True)
    minify_wspace = minify_opts.get("wspace", True)
    minify_comments = minify_opts.get("comments", True)

    if minify_wspace:
        return output_min_wspace(root, ctxt, minify_lines)
    else:
        return output_original_wspace(root, ctxt, minify_comments)
    
from pico_process import Source
