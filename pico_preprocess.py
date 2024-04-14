from utils import *

class CodeMapping(Tuple):
    """Specifies that code starting at index 'idx' maps to the given source starting at index 'src_idx'"""
    idx = src_path = src_code = src_idx = src_line = ...

k_long_brackets_re = re.compile(r"\[(=*)\[(.*?)\]\1\]", re.S)
k_wspace = " \t\r\n"

def preprocess_code(path, code, start_line=0, preprocessor=None):
    """preprocess the given pico8 code (e.g. handle #include-s)"""
    outparts = []
    outmappings = []
    i = start_i = out_i = 0
    
    if preprocessor is None:
        preprocessor = PicoPreprocessor()
    preprocessor.start(path, code, outparts)

    def skip_long_brackets():
        nonlocal i
        m = k_long_brackets_re.match(code, i)
        if m:
            i = m.end()
            return True

    def flush_output():
        nonlocal start_i, out_i
        if i > start_i and preprocessor.active:
            outparts.append(code[start_i:i])
            outmappings.append(CodeMapping(out_i, path, code, start_i, start_line))
            out_i += (i - start_i)
        start_i = i

    strict = preprocessor.strict

    while i < len(code):
        ch = code[i]

        if ch == '-' and list_get(code, i + 1) == '-' and strict: # comment
            i += 2
            if not skip_long_brackets():
                while list_get(code, i) not in ('\n', None):
                    i += 1

        elif ch == '[' and list_get(code, i + 1) == '[' and strict: # long string
            skip_long_brackets()

        elif ch in ('"', "'") and strict:
            i += 1
            while list_get(code, i) not in (ch, None):
                i += 2 if code[i] == '\\' else 1
            i += 1

        elif ch != '#':
            i += 1

        elif list_get(code, i + 1) == '[' and list_get(code, i + 2) != '[': # #[...] inline directive (not used by pico preprocessor)
            flush_output()
            i, start_i, out_i = preprocessor.handle_inline(path, code, i, start_i, out_i, outparts, outmappings)

        elif list_get(code, i + 1, '') not in k_wspace and list_get(code, i + 1) != '(': # normal directive?
            # is it at the start of the line? (potentially with some whitespace before)
            hash_i = i
            while list_get(code, i - 1, '') in k_wspace:
                if i == 0 or code[i - 1] == '\n':
                    break
                i -= 1
            else:
                i = hash_i + 1
                continue

            flush_output()
            i, start_i, out_i = preprocessor.handle(path, code, hash_i, start_i, out_i, outparts, outmappings)

        else:
            i += 1

    flush_output()
    preprocessor.finish(path, code, outparts)
    return "".join(outparts), outmappings

class PicoPreprocessor:
    """The standard pico8 preprocessor (supporting #include and nothing else)"""

    def __init__(m, strict=True, include_notifier=None):
        m.strict = strict
        m.include_notifier = include_notifier
        m.active = True # always
        
    def start(m, path, code, outparts):
        pass

    # note: we support recursive includes (unlike pico8) - it's pointless not to

    def read_included_cart(m, orig_path, inc_name, out_i, outparts, outmappings):
        tab_idx = None
        if re.fullmatch(r".*:[0-9a-fA-F]", inc_name):
            tab_idx = int(inc_name[-1], 16)
            inc_name = inc_name[:-2]

        inc_path = path_join(path_dirname(orig_path), inc_name)
        if not path_exists(inc_path):
            # windows path outside windows, maybe?
            inc_path = inc_path.replace("\\", "/")
            if not path_exists(inc_path):
                throw(f"cannot open included cart at: {inc_path}")
        
        if m.include_notifier:
            m.include_notifier(inc_path)

        inc_cart = read_cart(inc_path, preprocessor=m)
        if e(tab_idx):
            trim_cart_to_tab(inc_cart, tab_idx)

        if inc_cart.code_map:
            for map in inc_cart.code_map:
                outmappings.append(CodeMapping(out_i + map.idx, map.src_path, map.src_code, map.src_idx, map.src_line))
        else:
            outmappings.append(CodeMapping(out_i, inc_path, inc_cart.code, 0, 0))
        outparts.append(inc_cart.code)

        return out_i + len(inc_cart.code)

    def handle(m, path, code, i, start_i, out_i, outparts, outmappings):
        end_i = code.find("\n", i)
        end_i = end_i if end_i >= 0 else len(code)

        args = code[i:end_i].split(maxsplit=1)
        if len(args) == 2 and args[0] == "#include":
            out_i = m.read_included_cart(path, args[1], out_i, outparts, outmappings)
            return end_i, end_i, out_i
        else:
            return i + 1, start_i, out_i

    def handle_inline(m, path, code, i, start_i, out_i, outparts, outmappings):
        return i + 1, start_i, out_i
        
    def finish(m, path, code, outparts):
        pass

k_tab_break = "\n-->8\n" # yes, pico8 doesn't accept consecutive/initial/final tab breaks

def trim_cart_to_tab(cart, target_tab):
    tab = start = 0
    limit = len(cart.code)
    while start < limit:
        end = cart.code.find(k_tab_break, start)
        if end < 0:
            end = limit

        if tab == target_tab:
            break

        tab += 1
        start = end + len(k_tab_break)
    else:
        throw(f"Couldn't find tab {target_tab} in cart: {cart.path}")

    cart.code = cart.code[start:end]

    new_code_map = []
    for map in cart.code_map:
        if map.idx > end:
            break

        if map.idx <= start:
            new_code_map.clear()
        
        new_idx = max(map.idx - start, 0)
        new_src_idx = map.src_idx + (start if map.src_path == cart.path else 0)

        new_code_map.append(CodeMapping(new_idx, map.src_path, map.src_code, new_src_idx, map.src_line))
    cart.code_map = new_code_map

k_custom_pp_inline_delims = k_wspace + "[]"
    
class CustomPreprocessor(PicoPreprocessor):
    """A custom preprocessor that isn't enabled by default (and is quite quirky & weird)"""

    def __init__(m, defines=None, pp_handler=None, **kwargs):
        super().__init__(**kwargs)
        m.defines = defines.copy() if defines else {}
        m.pp_handler = pp_handler
        m.ppstack = []
        m.recurse = 0
        m.active = True
        
    def get_active(m):
        return m.ppstack[-1] if m.ppstack else True
        
    def start(m, path, code, outparts):
        if m.pp_handler:
            m.pp_handler(op=True, args=(), ppline="", active=True, outparts=outparts, negate=False)
        m.recurse += 1

    def parse_args(m, args, code, i, inline):
        while True:
            while str_get(code, i, '\0') in k_wspace:
                i += 1
            
            if str_get(code, i) == None:
                return None
            elif str_get(code, i) == ']' and inline:
                return i

            if str_get(code, i) == '[':
                match = k_long_brackets_re.match(code, i)
                if not match:
                    throw("Unterminated custom preprocessor long brackets")

                i = match.end()
                args.append(match.group(2))
            else:
                arg_i = i
                while str_get(code, i, '') not in (k_custom_pp_inline_delims if inline else k_wspace):
                    i += 1
                args.append(code[arg_i:i])

    def handle(m, path, code, i, start_i, out_i, outparts, outmappings):
        end_i = code.find("\n", i)
        while end_i >= 0 and code[end_i - 1] == '\\':
            end_i = code.find("\n", end_i + 1)

        end_i = end_i if end_i >= 0 else len(code)
        line = code[i:end_i].replace("\\\n", "\n")

        args = []
        m.parse_args(args, line, 0, inline=False)
        
        op = args[0] if args else ""

        if op == "#include" and len(args) == 2:
            if m.active:
                out_i = m.read_included_cart(path, args[1], out_i, outparts, outmappings)

        elif op == "#define" and len(args) >= 2:
            if m.active:
                value = line.split(maxsplit=2)[2].rstrip() if len(args) > 2 else ""
                if "#[" in value:
                    value, _ = preprocess_code("(define)", value, preprocessor=m)
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

        else:
            negate = False
            if op.startswith("#!"):
                op = str_replace_at(op, 1, 1, "")
                negate = True

            value = None
            if m.pp_handler:
                value = m.pp_handler(op=op, args=args, ppline=line, active=m.active, outparts=outparts, negate=negate)
            
            if value in (None, False):
                throw(f"Invalid custom preprocessor line: {line}")
            
            if isinstance(value, str) and value:
                outparts.append(value)
                out_i += len(value)

        return end_i, end_i, out_i
        
    def handle_inline(m, path, code, i, start_i, out_i, outparts, outmappings):
        if not m.active:
            return i + 1, start_i, out_i

        orig_i = i
        i += 2
        negate = False
        if list_get(code, i) == '!':
            i += 1
            negate = True

        args = []
        i = m.parse_args(args, code, i, inline=True)
        if i is None:
            throw("Unterminated custom preprocessor args")
        
        key = args[0] if args[0] else ""
        op = f"#[{key}]"

        end_i = i + 1
        ppline = code[orig_i:end_i]

        value = m.pp_handler(op=op, args=args, ppline=ppline, active=True, outparts=outparts, negate=negate) if m.pp_handler else None
        if value in (None, False):
            if len(args) == 1 and not negate:
                if key in m.defines:
                    value = m.defines[key]
                else:
                    throw(f"Undefined custom preprocessor variable: {key}")
            elif 2 <= len(args) <= 3:
                if (key in m.defines) ^ negate:
                    value = list_get(args, 1, "")
                else:
                    value = list_get(args, 2, "")
            else:
                throw(f"Wrong inline custom preprocessor directive: {ppline}")

        if value is True:
            value = ""
        if value:
            outparts.append(value)
        return end_i, end_i, out_i + len(value)

    def finish(m, path, code, outparts):
        m.recurse -= 1
        if m.recurse == 0 and m.ppstack:
            throw("Unterminated custom preprocessor ifs")
        if m.pp_handler:
            m.pp_handler(op=False, args=(), ppline="", active=True, outparts=outparts, negate=False)

from pico_cart import read_cart
