from utils import *
from pico_defs import *

def print_size(name, size, limit, prefix=None, handler=None):
    if handler and handler != True:
        handler(prefix, name, size, limit)
    else:
        percent = size / limit * 100
        fmt = "%.2f%%" if percent >= 95 else "%.0f%%"
        if prefix:
            name = f"{prefix} {name}"
        name += ":"
        print(name, size, fmt % percent)

def print_code_size(size, **kwargs):
    print_size("chars", size, 0xffff, **kwargs)

def print_compressed_size(size, **kwargs):
    print_size("compressed", size, k_code_size, **kwargs)

def write_code_size(cart, handler=None, input=False):
    print_code_size(len(cart.code), prefix="input" if input else None, handler=handler)

def write_compressed_size(cart, handler=True, debug_handler=None, **opts):
    compress_code(BinaryWriter(BytesIO()), cart.code, size_handler=handler, debug_handler=debug_handler,
                  force_compress=True, fail_on_error=False, **opts)

k_old_code_table = [
    None, '\n', ' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', # 00
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', # 0d
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', # 1a
    '!', '#', '%', '(', ')', '{', '}', '[', ']', '<', '>', # 27
    '+', '=', '/', '*', ':', ';', '.', ',', '~', '_' # 32
]

k_old_inv_code_table = {ch: i for i, ch in enumerate(k_old_code_table)}

k_old_compressed_code_header = b":c:\0"
k_new_compressed_code_header = b"\0pxa"

def update_mtf(mtf, idx, ch):
    for ii in range(idx, 0, -1):
        mtf[ii] = mtf[ii - 1]
    mtf[0] = ch

def uncompress_code(r, max_code_size=k_code_size, size_handler=None, debug_handler=None, **_):
    start_pos = r.pos()
    header = r.bytes(4, allow_eof=True)

    if header == k_new_compressed_code_header:
        # the new compression format - uses bit encoding & mtf (move-to-front)
        unc_size = r.u16()
        com_size = r.u16()

        if size_handler:
            print_compressed_size(com_size, prefix="input", handler=size_handler)
        
        mtf = [chr(i) for i in range(0x100)]
        br = BinaryBitReader(r.f)
        if debug_handler: debug_handler.init(br, str)
        
        code = []
        while len(code) < unc_size:
            if br.bit():
                extra = 0
                while br.bit():
                    extra += 1
                idx = br.bits(4 + extra) + make_mask(4, extra)
                
                if debug_handler: debug_handler.update(mtf[idx])
                code.append(mtf[idx])
                
                update_mtf(mtf, idx, code[-1])
            else:
                offlen = (5 if br.bit() else 10) if br.bit() else 15                
                offset = br.bits(offlen) + 1

                if offset == 1 and offlen != 5:
                    assert offlen == 10
                    startlen = len(code)
                    while True:
                        ch = br.bits(8)
                        if ch != 0:
                            code.append(chr(ch))
                        else:
                            break
                        
                    if debug_handler: debug_handler.update("".join(code[startlen:]))
                else:
                    count = 3
                    while True:
                        part = br.bits(3)
                        count += part
                        if part != 7:
                            break
                    
                    if debug_handler: debug_handler.update(Lz77Entry(offset, count))
                    for _ in range(count):
                        code.append(code[-offset])
        
        if debug_handler: debug_handler.end()
        assert r.pos() == start_pos + com_size
        assert len(code) == unc_size

    elif header == k_old_compressed_code_header:
        # the old compression format - byte-based and allows very limited matching
        unc_size = r.u16()
        assert r.u16() == 0 # ?
        if debug_handler: debug_handler.init(r, str)

        code = []
        while True:
            ch = r.u8()
            if ch == 0x00:
                ch2 = r.u8()
                if ch2 == 0x00:
                    break
                code.append(chr(ch2))
                if debug_handler: debug_handler.update(code[-1])

            elif ch <= 0x3b:
                code.append(k_old_code_table[ch])
                if debug_handler: debug_handler.update(code[-1])

            else:
                ch2 = r.u8()
                count = (ch2 >> 4) + 2
                offset = ((ch - 0x3c) << 4) + (ch2 & 0xf)
                assert count <= offset
                if debug_handler: debug_handler.update(Lz77Entry(offset, count))                
                for _ in range(count):
                    code.append(code[-offset])

        if size_handler:
            print_compressed_size(r.pos() - start_pos, prefix="input", handler=size_handler)

        if debug_handler: debug_handler.end()
        assert len(code) in (unc_size, unc_size - 1) # extra null at the end dropped?

    else:
        r.subpos(len(header))
        code = [chr(c) for c in r.zbytes(max_code_size, allow_eof=True)]

    return "".join(code)

def get_compressed_size(r, max_code_size=k_code_size):
    start_pos = r.pos()
    header = r.bytes(4, allow_eof=True)

    if header == k_new_compressed_code_header:
        r.u16()
        return r.u16() # compressed size

    elif header == k_old_compressed_code_header:
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
        r.subpos(len(header))
        return len(r.zbytes(max_code_size, allow_eof=True))

class Lz77Entry(Tuple):
    """A copy of 'count' bytes starting from an 'offset' to the left of the current position."""
    offset = count = ...

class Lz77Advance(Tuple):
    """A strategy that advances from 'i' to 'next_i' using 'item' (a literal/lz77/etc) with cost 'cost',
       it was preceded by Lz77Advance 'prev'. (so Lz77Advance-s form a linked list)
       ('ctxt' is the opaque context for measure)"""
    i = next_i = cost = ctxt = item = prev = ...

class SubMatchDict(Struct):
    """When the list of previous matches gets too long, a SubMatchDict can be used as a perf optimization,
       grouping the list by an extra code character"""
    dict = best_j = ...

def get_lz77(code, min_c=3, max_c=0x7fff, max_o=0x7fff, measure=None, min_cost=None,
             get_cheaper_c=None, max_o_steps=None, fast_c=None, no_repeat=False, litblock_idxs=None):
    """a generic helper that transforms code (either bytes or str) into a sequence of items:
         literals (bytes/chars), Lz77Entry-ies, and literal blocks.
       min_c/max_c - min/max allowed counts in Lz77Entry-ies
       max_o - max allowed offsets (distances) in Lz77Entry-ies
       measure - measures the cost of a particular item. (any cost unit can be used)
                 also returns a context, an opaque value passed when measuring subsequent items
       min_cost - the absolute minimum cost that the given number of bytes can correspond to
                  anywhere for any code. (used for perf. optimization)
       get_cheaper_c - given a count, return a smaller count that results in less cost
                       (but may be a better choice if the next match catches up without increasing cost)
       max_o_steps - (turn this to get_shorter_o?) - offset values that may be shorter but
                     result in less cost.
       litblock_idxs - indices of where to enter or exit a literal block (should be precomputed)
    """    
    min_matches = defaultdict(list) # for each min_c-sized sequence in the code - its previous matches
                                    # as either a list or a SubMatchDict
    next_litblock = litblock_idxs.popleft() if litblock_idxs else len(code)
    empty_code = type(code)() # e.g. "" if code is an str

    def get_match_length(left, left_i, right, right_i, min_c):
        c = min_c
        limit = min(len(left) - left_i, len(right) - right_i)
        while c < limit and left[left_i + c] == right[right_i + c]:
            c += 1
        return c

    def find_match(i, min_c=min_c, max_o=max_o, matches_dict=min_matches):
        """find the longest lz77 match at a given position"""
        matches = matches_dict[code[i:i+min_c]]

        if isinstance(matches, SubMatchDict):
            best_c, best_j = find_match(i, min_c + 1, max_o, matches.dict)
            if not best_c:
                c, j = min_c, matches.best_j
                if j >= 0:
                    if max_c != None:
                        c = min(c, max_c)
                    if no_repeat:
                        c = min(c, i - j)
                    
                    if not (max_o != None and j < i - max_o):
                        best_c, best_j = c, j
                
            return best_c, best_j

        best_c, best_j = 0, -1
        best_slice = empty_code

        for j in reversed(matches):
            if best_slice == code[j:j+best_c]: # some speed-up, esp. for cpython
                c = get_match_length(code, i, code, j, best_c if best_c > 0 else min_c)
            else:
                continue
                
            if max_c != None:
                c = min(c, max_c)
            if no_repeat:
                c = min(c, i - j)

            if max_o != None and j < i - max_o:
                break

            if c > best_c and c >= min_c or c == best_c and j > best_j:
                best_c, best_j = c, j
                best_slice = code[i:i+best_c]
        
        return best_c, best_j

    def convert_to_matches_dict(matches, min_i, c):
        """list -> SubMatchDict"""
        matches_dict = defaultdict(list)
        best_j = -1

        for j in matches:
            if max_o != None and j < min_i - max_o:
                continue
            
            matches_dict[code[j:j+c]].append(j)
            best_j = j
        
        return SubMatchDict(matches_dict, best_j)

    i = 0 # current position in the code
    prev_i = 0 # previous position in the code
    advances = deque() if measure else None # potentially worthwhile ways to go from the current or past positions
    curr_adv = None

    def add_advance(cost, ctxt, c, item):
        """add an Lz77Advance if it's worthwhile compared to existing ones"""
        next_i = i + c
        adv_idx = 0
        insert_idx = None
        do_replace = False
        for adv in advances:
            if insert_idx is None:
                if next_i == adv.next_i:
                    insert_idx, do_replace = adv_idx, True
                elif next_i < adv.next_i:
                    insert_idx = adv_idx

            if insert_idx != None:
                adv_cost = adv.cost
                if min_cost:
                    adv_cost -= min_cost(adv.next_i - next_i)

                if cost >= adv_cost:
                    return
            adv_idx += 1
        
        next_adv = Lz77Advance(i, next_i, cost, ctxt, item, curr_adv)
        if do_replace:
            advances[insert_idx] = next_adv
        elif insert_idx != None:
            advances.insert(insert_idx, next_adv)
        else:
            advances.append(next_adv)

    def add_lz77_advance(j, c):
        item = Lz77Entry(i - j, c)
        cost, ctxt = measure(curr_ctxt, item)
        add_advance(curr_cost + cost, ctxt, c, item)
    
    def get_advance_items(adv):
        while adv:
            yield adv.i, adv.item
            adv = adv.prev
    
    while i < len(code):
        if i >= next_litblock:
            if curr_adv: # get rid of any advances
                yield from reversed(tuple(get_advance_items(curr_adv)))
                curr_adv = None
                advances.clear()

            best_c = sys.maxsize
            end_litblock = litblock_idxs.popleft() if litblock_idxs else len(code)

            yield i, code[i:end_litblock]
            i = end_litblock

            next_litblock = litblock_idxs.popleft() if litblock_idxs else len(code)

        else:
            if measure:
                curr_ctxt = curr_adv.ctxt if curr_adv else None
                curr_cost = curr_adv.cost if curr_adv else 0

                # try using a literal
                ch_cost, ch_ctxt = measure(curr_ctxt, code[i])
                add_advance(curr_cost + ch_cost, ch_ctxt, 1, code[i])

                # try using a match
                best_c, best_j = find_match(i)
                if best_c > 0:
                    add_lz77_advance(best_j, best_c)
                
                    if get_cheaper_c:
                        # try a shorter yet cheaper match
                        cheap_c = get_cheaper_c(best_c)
                        if best_c > cheap_c >= min_c:
                            add_lz77_advance(best_j, cheap_c)

                    if max_o_steps:
                        # try a shorter yet closer match
                        for step in max_o_steps:
                            if i - best_j <= step:
                                break

                            sh_best_c, sh_best_j = find_match(i, max_o=step)
                            if sh_best_c > 0:
                                add_lz77_advance(sh_best_j, sh_best_c)
                                
                                if get_cheaper_c:
                                    # try a shorter yet cheaper match
                                    sh_cheap_c = get_cheaper_c(sh_best_c)
                                    if sh_best_c > sh_cheap_c >= min_c:
                                        add_lz77_advance(sh_best_j, sh_cheap_c)
                
                curr_adv = advances.popleft()
                i = curr_adv.next_i
                
                if not advances:
                    # have a best choice, flush it
                    yield from reversed(tuple(get_advance_items(curr_adv)))
                    curr_adv = None

            else: # case when no 'measure' is provided - result is far less optimal
                best_c, best_j = find_match(i)
                if best_c > 0:
                    # check for obvious wins of not using matches
                    skip_best_c, skip_best_j = find_match(i+1)
                    if skip_best_c > best_c:
                        yield i, code[i]
                        i += 1
                    else:
                        yield i, Lz77Entry(i - best_j, best_c)
                        i += best_c
                else:
                    yield i, code[i]
                    i += 1
        
        if fast_c is None or best_c < fast_c:
            # add the matches we just passed through to min_matches

            for j in range(prev_i, i):
                matches_dict = min_matches
                c = min_c
                matches = matches_dict[code[j:j+c]]
                
                while isinstance(matches, SubMatchDict):
                    matches.best_j = j
                    matches_dict = matches.dict
                    c += 1
                    matches = matches_dict[code[j:j+c]]
                
                matches.append(j)

                if len(matches) > 200 and len(matches_dict) > 5 and c < min_c * 6: # shaky perf. heuristic
                    matches_dict[code[j:j+c]] = convert_to_matches_dict(matches, i, c + 1)
            
        prev_i = i
    
    assert not curr_adv

def compress_code(w, code, size_handler=None, debug_handler=None, force_compress=False, 
                  fail_on_error=True, fast_compress=False, old_compress=False, **_):
    is_new = not old_compress
    min_c = 3
    
    if len(code) >= k_code_size or force_compress: # (>= due to null)
        start_pos = w.pos()
        w.bytes(k_new_compressed_code_header if is_new else k_old_compressed_code_header)
        w.u16(len(code) & 0xffff) # only throw under fail_on_error below
        len_pos = w.pos()
        w.u16(0) # revised below
                
        if is_new:
            # the new compression scheme, measured cost is in bits
            bw = BinaryBitWriter(w.f)
            if debug_handler: debug_handler.init(bw, str)
            mtf = [chr(i) for i in range(0x100)]

            def mtf_cost_heuristic(ch_i):
                mask = 1 << 4
                count = 6
                while ch_i >= mask:
                    mask = (mask << 1) | (1 << 4)
                    count += 2
                if ch_i >= 16:
                    count -= 1 # heuristic, since mtf generally pays forward
                return count

            def measure(ctxt_mtf, item):
                if isinstance(item, Lz77Entry):
                    offset_bits = max(round_up(count_significant_bits(item.offset - 1), 5), 5)
                    count_bits = (((item.count - min_c) // 7) + 1) * 3
                    cost = 2 + (offset_bits < 15) + offset_bits + count_bits

                else:
                    ctxt_mtf = ctxt_mtf or mtf                        
                    ch_i = ctxt_mtf.index(item)
                    cost = mtf_cost_heuristic(ch_i)

                    ctxt_mtf = ctxt_mtf[:] # a bit wasteful, but doesn't impact perf in practice
                    update_mtf(ctxt_mtf, ch_i, item)

                return cost, ctxt_mtf

            def min_cost(dist):
                # assume dist can be covered by an Lz77Entry without any overhead
                # plus subtract possible overhead *savings* of an Lz77Entry (due to diff. in offset_bits)
                return max((((dist - min_c) // 7) + 1) * 3 - 11, 0)

            # heuristicly find at which indices we should enter/leave literal blocks
            def preprocess_litblock_idxs():
                premtf = [chr(i) for i in range(0x100)]
                pre_min_c = 4 # ignore questionable lz77s
                last_cost_len = 0x20
                last_cost_mask = last_cost_len - 1
                last_costs = [0 for i in range(last_cost_len)] # cost deltas of using compression vs literal blocks
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

                for i, item in get_lz77(code, min_c=pre_min_c, fast_c=1):
                    if isinstance(item, Lz77Entry):
                        cost = (20 - item.count * 8) // item.count
                        for j in range(item.count):
                            add_last_cost(i + j, cost)
                    else:
                        ch_i = premtf.index(item)
                        update_mtf(premtf, ch_i, item)
                        cost = mtf_cost_heuristic(ch_i)
                        add_last_cost(i, cost - 8)                        

                for i in range(last_cost_len): # flush litblock
                    add_last_cost(len(code) + i, 0)

                return litblock_idxs
                    
            def write_match(item):
                bw.bit(0)
                offset_val = item.offset - 1
                count_val = item.count - min_c
                
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

            def write_litblock(str):
                bw.bit(0); bw.bit(1); bw.bit(0)
                bw.bits(10, 0)

                for ch in str:
                    bw.bits(8, ord(ch))
                bw.bits(8, 0)
            
            def get_cheaper_c(c):
                return round_down(c - min_c, 7) - 1 + min_c

            if fast_compress:
                items = get_lz77(code, min_c=min_c, max_c=None, fast_c=16)
            else:
                items = get_lz77(code, min_c=min_c, max_c=None, measure=measure, min_cost=min_cost,
                                 get_cheaper_c=get_cheaper_c, max_o_steps=(0x20, 0x400), litblock_idxs=preprocess_litblock_idxs())

            for i, item in items:
                if isinstance(item, Lz77Entry):
                    write_match(item)
                elif len(item) == 1:
                    write_literal(item)
                else:
                    write_litblock(item)
                if debug_handler: debug_handler.update(item)
                    
            if debug_handler: debug_handler.end()
            bw.flush()

        else:
            # the old compression scheme, measured cost is in bytes
            if debug_handler: debug_handler.init(w, str)

            def measure(ctxt, item):
                if isinstance(item, Lz77Entry):
                    return 2, ctxt
                elif item in k_old_inv_code_table:
                    return 1, ctxt
                else:
                    return 2, ctxt

            def write_match(item):
                offset_val = item.offset
                count_val = item.count - 2
                w.u8(0x3c + (offset_val >> 4))
                w.u8((offset_val & 0xf) + (count_val << 4))

            def write_literal(ch):
                ch_i = k_old_inv_code_table.get(ch, 0)
                
                if ch_i > 0:
                    w.u8(ch_i)
                
                else:
                    w.u8(0)
                    w.u8(ord(ch))

            for i, item in get_lz77(code, min_c=min_c, max_c=0x11, max_o=0xc3f, no_repeat=True,
                                    measure=None if fast_compress else measure):
                if isinstance(item, Lz77Entry):
                    write_match(item)
                else:
                    write_literal(item)
                if debug_handler: debug_handler.update(item)
                    
            if debug_handler: debug_handler.end()

        size = w.pos() - start_pos
        if size_handler:
            print_compressed_size(size, handler=size_handler)
        
        if fail_on_error:
            check(len(code) < 0x10000, "cart has too many characters!")
            check(size <= k_code_size, "cart takes too much compressed space!")
        
        if is_new:   
            w.setpos(len_pos)
            w.u16(size & 0xffff) # only throw under fail_on_error above
            
    else:
        w.bytes(encode_p8str(code))

class CompressionTracer:
    """a debug_handler that traces compression to a file"""
    def __init__(m, path, lang):
        m.file = file_create_maybe_text(path)
        m.lang = lang

    def init(m, reader, type):
        m.reader = reader
        m.old_pos = m.curr_pos()
        m.code = []
        m.type = type
    
    def curr_pos(m):
        if isinstance(m.reader, (BinaryBitReader, BinaryBitWriter)):
            return m.reader.bit_position
        elif isinstance(m.reader, (BinaryReader, BinaryWriter)):
            return m.reader.position
        fail()

    def escape(m, value):
        if not isinstance(value, str):
            value = value.decode(errors="backslashreplace") # we don't pre-escape \\, so the result isn't properly parsable
        return '"%s"' % from_langstr(value, m.lang).replace('"', '""') # let \n/etc go unescaped, good for excel/etc

    def update(m, item):
        pos = m.curr_pos()
        size = pos - m.old_pos

        if isinstance(item, Lz77Entry):
            for _ in range(item.count):
                m.code.append(m.code[-item.offset])
            
            if m.type is str:
                old_code = "".join(m.code[-item.count:])
            else:
                old_code = bytes(m.code[-item.count:])

            m.file.write(f"{size},{m.escape(old_code)},{item.offset}:{item.count}\n")

        else:
            for ch in item:
                m.code.append(ch)
            m.file.write(f"{size},{m.escape(item)}\n")

        m.old_pos = pos

    def end(m):
        m.file.close()
