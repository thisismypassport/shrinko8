from utils import *
from pico_defs import *

def print_size(name, size, limit, prefix=None, handler=None):
    if handler and handler != True:
        handler(prefix, name, size, limit)
    else:
        percent = size / limit * 100
        fmt = "%.2f%%" if percent >= 95 else "%.0f%%"
        if prefix:
            name = "%s %s" % (prefix, name)
        name += ":"
        print(name, size, fmt % percent)

def print_code_size(size, **kwargs):
    print_size("chars", size, 0xffff, **kwargs)

def print_compressed_size(size, **kwargs):
    print_size("compressed", size, k_code_size, **kwargs)

def write_code_size(cart, handler=None, input=False):
    print_code_size(len(cart.code), prefix="input" if input else None, handler=handler)

def write_compressed_size(cart, handler=True, **opts):
    compress_code(BinaryWriter(BytesIO()), cart.code, size_handler=handler, force_compress=True, fail_on_error=False, **opts)

k_code_table = [
    None, '\n', ' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', # 00
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', # 0d
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', # 1a
    '!', '#', '%', '(', ')', '{', '}', '[', ']', '<', '>', # 27
    '+', '=', '/', '*', ':', ';', '.', ',', '~', '_' # 32
]

k_inv_code_table = {ch: i for i, ch in enumerate(k_code_table)}

k_compressed_code_header = b":c:\0"
k_new_compressed_code_header = b"\0pxa"

def update_mtf(mtf, idx, ch):
    for ii in range(idx, 0, -1):
        mtf[ii] = mtf[ii - 1]
    mtf[0] = ch

def uncompress_code(r, size_handler=None, **_):
    start_pos = r.pos()
    header = r.bytes(4, allow_eof=True)

    if header == k_new_compressed_code_header:
        unc_size = r.u16()
        com_size = r.u16()

        if size_handler:
            print_compressed_size(com_size, prefix="input", handler=size_handler)
        
        mtf = [chr(i) for i in range(0x100)]
        br = BinaryBitReader(r.f)
        
        code = []
        while len(code) < unc_size:
            #last_bit_pos = br.bit_position
            if br.bit():
                extra = 0
                while br.bit():
                    extra += 1
                idx = br.bits(4 + extra) + make_mask(4, extra)
                
                #print(len(code), ord(mtf[idx]), br.bit_position - last_bit_pos)
                code.append(mtf[idx])
                
                update_mtf(mtf, idx, code[-1])
            else:
                offlen = (5 if br.bit() else 10) if br.bit() else 15                
                offset = br.bits(offlen) + 1

                if offset == 1 and offlen != 5:
                    assert offlen == 10
                    while True:
                        ch = br.bits(8)
                        if ch != 0:
                            code.append(chr(ch))
                        else:
                            break
                    #print("******", br.bit_position - last_bit_pos)
                
                else:
                    count = 3
                    while True:
                        part = br.bits(3)
                        count += part
                        if part != 7:
                            break
                    
                    #print(len(code), "%s:%s" % (offset - 1, count - 3), br.bit_position - last_bit_pos)
                    for _ in range(count):
                        code.append(code[-offset])
        
        assert r.pos() == start_pos + com_size
        assert len(code) == unc_size

    elif header == k_compressed_code_header:
        unc_size = r.u16()
        assert r.u16() == 0 # ?

        code = []
        while True:
            ch = r.u8()
            if ch == 0x00:
                ch2 = r.u8()
                if ch2 == 0x00:
                    break
                code.append(chr(ch2))
            elif ch <= 0x3b:
                code.append(k_code_table[ch])
            else:
                ch2 = r.u8()
                count = (ch2 >> 4) + 2
                offset = ((ch - 0x3c) << 4) + (ch2 & 0xf)
                assert count <= offset
                for _ in range(count):
                    code.append(code[-offset])

        if size_handler:
            print_compressed_size(r.pos() - start_pos, prefix="input", handler=size_handler)

        assert len(code) in (unc_size, unc_size - 1) # extra null at the end dropped?

    else:
        r.addpos(-len(header))
        code = [chr(c) for c in r.zbytes(k_code_size, allow_eof=True)]

    return "".join(code)

def get_compressed_size(r):
    start_pos = r.pos()
    header = r.bytes(4, allow_eof=True)

    if header == k_new_compressed_code_header:
        r.u16()
        return r.u16() # compressed size

    elif header == k_compressed_code_header:
        r.u16()
        r.u16()
        
        while True:
            ch = r.u8()
            if ch == 0:
                if r.u8() == 0:
                    break
            elif ch > 0x3b:
                r.u8()

        return r.pos() - start_pos

    else:
        r.addpos(-len(header))
        return len(r.zbytes(k_code_size))

class Lz77Tuple(Tuple):
    fields = ("off", "cnt")

def get_lz77(code, min_c=3, max_c=0x7fff, max_o=0x7fff, measure_c=None, measure=None, max_o_steps=None, fast_c=None):
    min_matches = defaultdict(list)

    def get_match_length(left, left_i, right, right_i, min_c):
        c = min_c
        limit = min(len(left) - left_i, len(right) - right_i)
        while c < limit and left[left_i + c] == right[right_i + c]:
            c += 1
        return c

    def find_match(i, max_o=max_o):
        best_c, best_j = -1, -1
        for j in min_matches[code[i:i+min_c]]:
            if e(max_o) and j < i - max_o:
                continue

            if best_c >= 0:
                if code[i:i+best_c] == code[j:j+best_c]: # some speed-up, esp. for cpython
                    c = get_match_length(code, i, code, j, best_c)
                else:
                    continue
            else:
                c = get_match_length(code, i, code, j, min_c)

            if e(max_c):
                c = min(c, max_c)

            if c > best_c and c >= min_c or c == best_c and j > best_j:
                best_c, best_j = c, j
        
        return best_c, best_j

    def mktuple(i, j, count):
        return Lz77Tuple(i - j - 1, count - min_c)

    i = 0
    prev_i = 0
    while i < len(code):
        best_c, best_j = find_match(i)

        if best_c >= 0 and measure and best_c <= measure_c:
            lz_cost = measure(i, mktuple(i, best_j, best_c))
            ch_cost = measure(i, *code[i:i+best_c])
            if ch_cost < lz_cost:
                best_c = -1

        if best_c >= 0:
            best_cp1, best_jp1 = find_match(i+1)
            if measure and best_cp1 in (best_c, best_c - 1):
                lz_cost = measure(i, mktuple(i, best_j, best_c), *code[best_j:best_j+(1 + best_cp1 - best_c)])
                p1_cost = measure(i, code[i], mktuple(i + 1, best_jp1, best_cp1))
                if p1_cost < lz_cost:
                    best_c = -1

            # this one is too specific...
            if measure and best_c >= 0:
                best_cp2, best_jp2 = find_match(i+2)
                if best_cp2 == best_c:
                    lz_cost = measure(i, mktuple(i, best_j, best_c), *code[best_j:best_j+2])
                    p2_cost = measure(i, *code[i:i+2], mktuple(i + 2, best_jp2, best_cp2))
                    if p2_cost < lz_cost:
                        best_c = -1
                else:
                    best_cp2 = -1

                if best_cp2 > best_cp1:
                    best_cp1 = best_cp2

            if best_cp1 > best_c:
                yield i, code[i]
                i += 1
                continue

            if measure and max_o_steps:
                for step in max_o_steps:
                    if i - best_j <= step:
                        break

                    best_cs, best_js = find_match(i, max_o=step)
                    if best_cs >= 0:
                        best_cs2, best_js2 = find_match(i + best_cs)
                        best_c2, best_j2 = find_match(i + best_c)
                        if best_cs + best_cs2 >= best_c + best_c2 and best_c2 >= 0:
                            lz_cost = measure(i, mktuple(i, best_j, best_c), mktuple(i + best_c, best_j2, best_c2))
                            s2_cost = measure(i, mktuple(i, best_js, best_cs), mktuple(i + best_cs, best_js2, best_cs2))
                            if s2_cost < lz_cost:
                                best_c, best_j = best_cs, best_js
                                break

        if best_c >= 0:
            yield i, mktuple(i, best_j, best_c)
            i += best_c
        else:
            yield i, code[i]
            i += 1
            
        if not (e(fast_c) and best_c >= fast_c):
            for j in range(prev_i, i):
                min_matches[code[j:j+min_c]].append(j)
        prev_i = i

def compress_code(w, code, size_handler=None, force_compress=False, fail_on_error=True, fast_compress=False, old_compress=False, **_):
    is_new = not old_compress
    min_c = 3
    
    if len(code) >= k_code_size or force_compress: # (>= due to null)
        start_pos = w.pos()
        w.bytes(k_new_compressed_code_header if is_new else k_compressed_code_header)
        w.u16(len(code) & 0xffff)
        len_pos = w.pos()
        w.u16(0) # revised below
                
        if is_new:
            bw = BinaryBitWriter(w.f)
            mtf = [chr(i) for i in range(0x100)]

            def mtf_cost(ch_i):
                mask = 1 << 4
                count = 6
                while ch_i >= mask:
                    mask = (mask << 1) | (1 << 4)
                    count += 2
                return count

            def measure(i, *items):
                count = 0
                mtfcopy = None

                for item in items:
                    if isinstance(item, Lz77Tuple):
                        offset_bits = max(round_up(count_significant_bits(item.off), 5), 5)
                        count_bits = ((item.cnt // 7) + 1) * 3
                        count += 2 + (offset_bits < 15) + offset_bits + count_bits
                        i += item.cnt + min_c

                    else:
                        if mtfcopy is None:
                            mtfcopy = mtf[:]
                            
                        ch_i = mtfcopy.index(item)

                        cost = mtf_cost(ch_i)
                        if ch_i >= 16:
                            cost -= 2 # heuristic, since mtf generally pays forward

                        update_mtf(mtfcopy, ch_i, item)
                        count += cost
                        i += 1

                return count

            def preprocess_litblock_idxs():
                premtf = [chr(i) for i in range(0x100)]
                pre_min_c = 4 # ignore questionable lz77s
                last_cost_len = 0x20
                last_cost_mask = last_cost_len - 1
                last_costs = [0 for i in range(last_cost_len)]
                sum_costs = 0
                litblock_idxs = deque()

                in_litblock = False
                def add_last_cost(i, cost):
                    nonlocal sum_costs, in_litblock

                    cost_i = i & last_cost_mask
                    sum_costs -= last_costs[cost_i]
                    last_costs[cost_i] = cost
                    sum_costs += cost

                    if i >= last_cost_len and (not in_litblock and sum_costs > 19) or (in_litblock and sum_costs < 0):
                        in_litblock = not in_litblock

                        ordered_costs = last_costs[cost_i + 1:] + last_costs[:cost_i + 1]
                        best_func = max if in_litblock else min
                        best_j = best_func(range(last_cost_len), key=lambda j: sum(ordered_costs[-j-1:]))

                        litblock_idxs.append(i - best_j)

                for i, item in get_lz77(code, min_c=pre_min_c, fast_c=0):
                    if isinstance(item, Lz77Tuple):
                        count = item.cnt + pre_min_c
                        cost = (20 - count * 8) // count
                        for j in range(count):
                            add_last_cost(i + j, cost)
                    else:
                        ch_i = premtf.index(item)
                        update_mtf(premtf, ch_i, item)
                        cost = mtf_cost(ch_i) - 8
                        if cost > 0:
                            cost -= 2 # hueristic due to mtf generally paying it forward (also makes entering litblock much harder)
                        add_last_cost(i, cost)                        

                for i in range(last_cost_len): # flush litblock
                    add_last_cost(len(code) + i, 0)

                return litblock_idxs
                    
            def write_match(offset_val, count_val):
                bw.bit(0)
                
                offset_bits = max(round_up(count_significant_bits(offset_val), 5), 5)
                assert offset_bits in (5, 10, 15)
                bw.bit(offset_bits < 15)
                if offset_bits < 15:
                    bw.bit(offset_bits < 10)
                bw.bits(offset_bits, offset_val)
                
                while count_val >= 7:
                    bw.bits(3, 7)
                    count_val -= 7
                bw.bits(3, count_val)

            def write_literal(ch):
                bw.bit(1)
                ch_i = mtf.index(ch)
                
                i_val = ch_i 
                i_bits = 4
                while i_val >= (1 << i_bits):
                    bw.bit(1)
                    i_val -= 1 << i_bits
                    i_bits += 1
                    
                bw.bit(0)
                bw.bits(i_bits, i_val)
                                
                update_mtf(mtf, ch_i, ch)

            if fast_compress:
                litblock_idxs, in_litblock, next_litblock = (), False, sys.maxsize

                items = get_lz77(code, min_c=min_c, max_c=None, fast_c=16)
            else:
                litblock_idxs = preprocess_litblock_idxs()
                in_litblock = False
                next_litblock = litblock_idxs.popleft() if litblock_idxs else len(code)

                items = get_lz77(code, min_c=min_c, max_c=None, measure=measure, measure_c=3, max_o_steps=(0x20, 0x400))

            for i, item in items:
                #last_bit_pos = bw.bit_position
                if i >= next_litblock:
                    in_litblock = not in_litblock
                    next_litblock = litblock_idxs.popleft() if litblock_idxs else len(code)
                    if in_litblock:
                        #print(i, "******", (next_litblock - i) * 8 + 19)
                        bw.bit(0); bw.bit(1); bw.bit(0)
                        bw.bits(10, 0)
                    else:
                        bw.bits(8, 0)

                if in_litblock:
                    if isinstance(item, Lz77Tuple):
                        for j in range(item.cnt + min_c):
                            bw.bits(8, ord(code[i - item.off - 1 + j]))
                    else:
                        bw.bits(8, ord(item))
                else:
                    if isinstance(item, Lz77Tuple):
                        write_match(item.off, item.cnt)
                        #print(i, "%s:%s" % (item.off, item.cnt), bw.bit_position - last_bit_pos)
                    else:
                        write_literal(item)
                        #print(i, ord(item), bw.bit_position - last_bit_pos)
                    
            bw.flush()

        else:
            def write_match(offset_val, count_val):
                offset_val += 1
                count_val += 1
                w.u8(0x3c + (offset_val >> 4))
                w.u8((offset_val & 0xf) + (count_val << 4))

            def write_literal(ch):
                ch_i = k_inv_code_table.get(ch, 0)
                
                if ch_i > 0:
                    w.u8(ch_i)
                
                else:
                    w.u8(0)
                    w.u8(ord(ch))

            for i, item in get_lz77(code, min_c=min_c, max_c=0x11, max_o=0xc3f):
                if isinstance(item, Lz77Tuple):
                    write_match(item.off, item.cnt)
                else:
                    write_literal(item)

        size = w.pos() - start_pos
        if size_handler:
            print_compressed_size(size, handler=size_handler)
        
        if fail_on_error:
            assert len(code) < 0x10000, "cart has too many characters!"
            assert w.pos() <= k_cart_size, "cart takes too much compressed space!"
        
        if is_new:   
            w.setpos(len_pos)
            w.u16(size)
            
    else:
        w.bytes(bytes(ord(c) for c in code))
