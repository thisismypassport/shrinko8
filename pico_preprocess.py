from utils import *

class CodeMapping(Tuple):
    """Specifies that code starting at index 'idx' maps to the given source starting at index 'src_idx'"""
    idx = src_path = src_code = src_idx = src_line = ...

k_long_brackets_re = re.compile(r"\[(=*)\[(.*?)\]\1\]", re.S)
k_wspace = " \t\r\n"

def preprocess_code(path, code, start_line=0, **opts):
    """preprocess the given pico8 code (e.g. handle #include-s)"""
    outparts = []
    outmappings = []
    i = start_i = out_i = 0
    
    def skip_long_brackets():
        nonlocal i
        m = k_long_brackets_re.match(code, i)
        if m:
            i = m.end()
            return True

    def flush_output():
        nonlocal start_i, out_i
        if i > start_i:
            outparts.append(code[start_i:i])
            outmappings.append(CodeMapping(out_i, path, code, start_i, start_line))
            out_i += (i - start_i)
        start_i = i

    while i < len(code):
        ch = code[i]

        if ch == '-' and list_get(code, i + 1) == '-': # comment
            i += 2
            if not skip_long_brackets():
                while list_get(code, i) not in ('\n', None):
                    i += 1

        elif ch == '[' and list_get(code, i + 1) == '[': # long string
            skip_long_brackets()

        elif ch in ('"', "'"): # string
            i += 1
            while list_get(code, i) not in (ch, None):
                i += 2 if code[i] == '\\' else 1
            i += 1

        elif ch != '#':
            i += 1

        elif list_get(code, i + 1, '') not in k_wspace and list_get(code, i + 1) != '(': # normal directive
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
            end_i = code.find("\n", hash_i)
            end_i = end_i if end_i >= 0 else len(code)

            args = code[hash_i:end_i].split(maxsplit=1)
            if len(args) == 2 and args[0] == "#include":
                out_i = read_included_cart(path, args[1], out_i, outparts, outmappings, **opts)
                i, start_i, out_i = end_i, end_i, out_i
            else:
                i = hash_i + 1

        else:
            i += 1

    flush_output()
    return "".join(outparts), outmappings

def read_included_cart(orig_path, inc_name, out_i, outparts, outmappings, include_notifier=None, **opts):
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
    
    if include_notifier:
        include_notifier(inc_path)

    inc_cart = read_cart(inc_path, **opts)
    if e(tab_idx):
        trim_cart_to_tab(inc_cart, tab_idx)

    if inc_cart.code_map:
        for map in inc_cart.code_map:
            outmappings.append(CodeMapping(out_i + map.idx, map.src_path, map.src_code, map.src_idx, map.src_line))
    else:
        outmappings.append(CodeMapping(out_i, inc_path, inc_cart.code, 0, 0))
    outparts.append(inc_cart.code)

    return out_i + len(inc_cart.code)

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

from pico_cart import read_cart
