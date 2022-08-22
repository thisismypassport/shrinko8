from utils import *
from sdl2_utils import Surface, BlendMode
from pico_defs import *
import hashlib, base64

k_latest_version_id = 36
k_latest_version_hex = 0x00020402 # v0.2.4c
k_default_platform = 'w' # also 'l', 'x'

class CartFormat(Enum):
    values = ("auto", "p8", "png", "lua", "rom", "clip", "url", "code")

    _output_values = tuple(value for value in values if value != "auto")
    _ext_values = tuple(value for value in _output_values if value != "code")
    _src_values = ("p8", "lua", "code")

class CodeMapping(Tuple):
    fields = ("idx", "src_name", "src_code", "src_idx", "src_line")

class Cart:
    def __init__(m):
        m.version_id = k_latest_version_id
        m.version_hex = k_latest_version_hex
        m.platform = k_default_platform
        m.rom = Memory(k_rom_size)
        m.name = ""
        m.code = ""
        m.code_map = ()
        m.screenshot = None
        m.meta = defaultdict(list)

    def copy(m):
        return deepcopy(m)

    def get_title(m):
        title = m.meta.get("title")
        if title is None:
            title = []
            for line in m.code.splitlines()[:2]:
                if line.startswith("--"):
                    title.append(line[2:].strip())
        return title

    def set_title(m, title):
        m.meta["title"] = title

    def set_code(m, code):
        title = m.get_title()
        m.code = code
        if title != m.get_title():
            m.set_title(title)

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

def read_code_from_rom(r, print_sizes=False, **_):
    start_pos = r.pos()
    header = r.bytes(4)

    if header == k_new_compressed_code_header:
        unc_size = r.u16()
        com_size = r.u16()

        if print_sizes:
            print_compressed_size(com_size, "input ")
        
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

        if print_sizes:
            print_compressed_size(r.pos() - start_pos, "input ")

        assert len(code) in (unc_size, unc_size - 1) # extra null at the end dropped?

    else:
        r.addpos(-4)
        code = [chr(c) for c in r.zbytes(k_code_size)]

    if print_sizes:
        print_code_size(len(code), "input ")    
    
    return "".join(code)

def read_cart_from_rom(buffer, path=None, **opts):
    cart = Cart()
    
    with BinaryReader(BytesIO(buffer), big_end = True) as r:
        cart.name = path_basename(path)
        cart.rom.replace(r.bytes(k_rom_size))
        cart.code = read_code_from_rom(r, **opts)

        r.setpos(k_cart_size)
        if r.pos() < r.len():
            cart.version_id = r.u8()
            cart.version_hex = r.u8() << 16
            cart.version_hex |= r.u16() << 8
            cart.platform = chr(r.u8())
            cart.version_hex |= r.u8()
            hash = r.bytes(20)

            if hash != bytes(20) and hash != hashlib.sha1(buffer[:k_cart_size]).digest():
                raise Exception("corrupted cart (wrong hash)")

    return cart

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

def print_size(name, size, limit):
    percent = size / limit * 100
    fmt = "%.2f%%" if percent >= 95 else "%.0f%%"
    print(name, size, fmt % percent)

def print_code_size(size, prefix=""):
    print_size(prefix + "chars:", size, 0xffff)

def print_compressed_size(size, prefix=""):
    print_size(prefix + "compressed:", size, k_code_size)

def write_code_to_rom(w, code, print_sizes=False, force_compress=False, fail_on_error=True, fast_compress=False, **_):
    k_new = True
    min_c = 3
    
    if print_sizes:
        print_code_size(len(code))

    if len(code) >= k_code_size or force_compress: # (>= due to null)
        start_pos = w.pos()
        w.bytes(k_new_compressed_code_header if k_new else k_compressed_code_header)
        w.u16(len(code) & 0xffff)
        len_pos = w.pos()
        w.u16(0) # revised below
                
        if k_new:
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
        if print_sizes:
            print_compressed_size(size)
        
        if fail_on_error:
            assert len(code) < 0x10000, "cart has too many characters!"
            assert w.pos() <= k_cart_size, "cart takes too much compressed space!"
        
        if k_new:   
            w.setpos(len_pos)
            w.u16(size)
            
    else:
        w.bytes(bytes(ord(c) for c in code))

def write_code_sizes(code, **opts):
    write_code_to_rom(BinaryWriter(BytesIO()), code, print_sizes=True, force_compress=True, fail_on_error=False, **opts)

def write_cart_to_rom(cart, with_trailer=False, **opts):
    io = BytesIO(bytearray(k_cart_size + (k_trailer_size if with_trailer else 0)))

    with BinaryWriter(io, big_end = True) as w:
        w.bytes(cart.rom.get_block(0, k_rom_size))        
        write_code_to_rom(w, cart.code, **opts)

        if with_trailer:
            w.setpos(k_cart_size)
            w.u8(cart.version_id)
            w.u8(cart.version_hex >> 24)
            w.u16((cart.version_hex >> 8) & 0xffff)
            w.u8(ord(cart.platform))
            w.u8(cart.version_hex & 0xff)
            w.bytes(hashlib.sha1(io.getvalue()[:k_cart_size]).digest())

        return io.getvalue()

k_cart_image_width, k_cart_image_height = 160, 205
k_screenshot_rect = Rect(0, 0, 128, 128)
k_screenshot_offset = Point(16, 24)
k_title_offset = Point(18, 167)

k_palette_map_6bpp = {Color(c.r & ~3, c.g & ~3, c.b & ~3, c.a & ~3): i for c, i in k_palette_map.items()}

def load_cart_image(f):
    r = BinaryReader(f)
    if r.bytes(8) != b"\x89PNG\r\n\x1a\n":
        raise Exception("Not a valid png")
    r.subpos(8)

    image = Surface.load(f)
    if image.width != k_cart_image_width or image.height != k_cart_image_height:
        raise Exception("Png has wrong size")

    return image

def read_cart_from_image(data, **opts):
    image = load_cart_image(BytesIO(data))
    width, height = image.size

    data = bytearray()
    screenshot = MultidimArray(k_screenshot_rect.size, 0)
    image.lock()

    for y in range(height):
        for x in range(width):
            r, g, b, a = image.get_at((x,y))
            byte = ((b & 3) << 0) | ((g & 3) << 2) | ((r & 3) << 4) | ((a & 3) << 6)
            data.append(byte)

    for y in range(k_screenshot_rect.h):
        for x in range(k_screenshot_rect.w):
            r, g, b, a = image.get_at(Point(x, y) + k_screenshot_offset)
            screenshot[x, y] = k_palette_map_6bpp.get((r & ~3, g & ~3, b & ~3, a & ~3), 0)

    image.unlock()

    cart = read_cart_from_rom(data, **opts)
    cart.screenshot = screenshot
    return cart
    
def write_cart_to_image(cart, res_path=None, screenshot_path=None, title=None, **opts):
    output = write_cart_to_rom(cart, with_trailer=True, **opts)

    if res_path is None:
        res_path = path_dirname(path_resolve(__file__))
    
    with file_open(path_join(res_path, "template.png")) as template_f:
        image = load_cart_image(template_f)
        width, height = image.size

        if screenshot_path:
            with file_open(screenshot_path) as screenshot_f:
                screenshot_surf = Surface.load(screenshot_f)
                screenshot_surf.blend_mode = BlendMode.none
                image.draw(screenshot_surf, k_screenshot_offset, k_screenshot_rect)
        elif cart.screenshot:
            screenshot_surf = Surface.create(*k_screenshot_rect.size)
            screenshot_surf.lock()
            for y in range(k_screenshot_rect.h):
                for x in range(k_screenshot_rect.w):
                    screenshot_surf.set_at((x, y), k_palette[cart.screenshot[x, y]])
            screenshot_surf.unlock()
            image.draw(screenshot_surf, k_screenshot_offset, k_screenshot_rect)
        
        if title is None:
            title = "\n".join(cart.get_title())
        if title:
            with file_open(path_join(res_path, "font.png")) as font_f:
                font_surf = Surface.load(font_f)
                x, y = 0, 0
                for ch in to_pico_chars(title):
                    chi = ord(ch)
                    chrect = Rect(chi % 16 * 8, chi // 16 * 6, 8 if chi >= 0x80 else 4, 6)
                    if ch == '\n' or x + chrect.w > 124:
                        x = 0
                        y += 8
                        if y >= 16:
                            break
                        elif ch == '\n':
                            continue
                    image.draw(font_surf, k_title_offset + Point(x, y), chrect)
                    x += chrect.w
        
        image.lock()
        for y in range(height):
            for x in range(width):
                i = x + y * width
                byte = output[i]
                r, g, b, a = image.get_at((x,y))
                b = (b & ~3) | (byte & 3)
                g = (g & ~3) | ((byte >> 2) & 3)
                r = (r & ~3) | ((byte >> 4) & 3)
                a = (a & ~3) | ((byte >> 6) & 3)
                image.set_at((x, y), (r, g, b, a))
        image.unlock()

        f = BytesIO()
        image.save(f)
        return f.getvalue()

k_meta_prefix = "meta:"
        
def read_cart_from_source(data, path=None, raw=False, preprocessor=None, **_):
    cart = Cart()
    
    def nybbles(line):
        for b in line:
            yield int(b, 16)
    
    def nybble_groups(line, n):
        for i in range(0, len(line), n):
            yield nybbles(line[i:i+n])
    
    def bytes(line):
        for i in range(0, len(line), 2):
            yield int(line[i] + line[i + 1], 16)
    
    def ext_nybbles(line):
        for b in line:
            if 'v' >= b.lower() >= 'g':
                yield ord(b.lower()) - ord('g') + 16
            else:
                yield int(b, 16)
    
    header = "lua" if raw else None
    code = []
    code_line = 0
    y = 0
    for line_i, line in enumerate(data.split("\n")): # not splitlines, that eats a trailing empty line
        clean = line.strip()
            
        if line.startswith("__") and clean.endswith("__") and not raw: # may end with whitespace
            header = clean[2:-2]
            y = 0
            
        elif header == "lua":
            if y == 0:
                code_line = line_i
            else:
                code.append("\n")
            code.append(to_pico_chars(line))
            y += 1
            
        elif header == "gfx" and clean:
            assert len(clean) == 0x80
            x = 0
            for b in nybbles(clean):
                cart.rom.set4(mem_tile_addr(x, y), b)
                x += 1
            y += 1
                
        elif header == "map" and clean:
            assert len(clean) == 0x100
            x = 0
            for b in bytes(clean):
                cart.rom.set8(mem_map_addr(x, y), b)
                x += 1
            y += 1
                
        elif header == "gff" and clean:
            assert len(clean) == 0x100
            x = 0
            for b in bytes(clean):
                cart.rom.set8(mem_flag_addr(x, y), b)
                x += 1
            y += 1
            
        elif header == "sfx" and clean:
            assert len(clean) == 0xa8
            x = 0
            for b in bytes(clean[:8]):
                cart.rom.set8(mem_sfx_info_addr(y, x), b)
                x += 1
            x = 0
            for bph, bpl, bw, bv, be in nybble_groups(clean[8:], 5):
                value = bpl | ((bph & 0x3) << 4) | ((bw & 0x7) << 6) | ((bv & 0x7) << 9) | ((be & 0x7) << 12) | ((bw & 0x8) << 12) 
                cart.rom.set16(mem_sfx_addr(y, x), value)
                x += 1
            y += 1
            
        elif header == "music" and clean:
            assert len(clean) == 0xb and clean[2] == ' '
            x = 0
            flags = next(bytes(clean[:2]))
            for b in bytes(clean[3:]):
                value = b | (((flags >> x) & 1) << 7) 
                cart.rom.set8(mem_music_addr(y, x), value)
                x += 1
            y += 1

        elif header == "label" and clean:
            assert len(clean) == 0x80
            if cart.screenshot is None:
                cart.screenshot = MultidimArray(k_screenshot_rect.size, 0)
            x = 0
            for b in ext_nybbles(clean):
                cart.screenshot[x, y] = b
                x += 1
            y += 1

        elif header and header.startswith(k_meta_prefix):
            cart.meta[header[len(k_meta_prefix):]].append(line.rstrip('\n'))
            
        elif header == None and clean.startswith("version "):
            cart.version_id = int(clean.split()[1])
            
    cart.name = path_basename(path)
    cart.code, cart.code_map = preprocess_code(cart.name, path, "".join(code), code_line, preprocessor=preprocessor)
    return cart

def write_cart_to_source(cart, **_):
    lines = ["pico-8 cartridge // http://www.pico-8.com"]
    lines.append("version %d" % cart.version_id)

    def nybbles(data):
        return "".join('%01x' % b for b in data)
    
    def nybble_groups(data):
        return "".join([nybbles(group) for group in data])
    
    def bytes(data):
        return "".join('%02x' % b for b in data)

    def ext_nybbles(data):
        return "".join(('%01x' % b if b < 16 else chr(b - 16 + ord('g'))) for b in data)

    def remove_empty_section_lines(num_spaces=0):
        while True:
            line = lines[-1]
            if line.startswith("__"):
                lines.pop()
                break
            elif line.count('0') == len(line) - num_spaces:
                lines.pop()
            else:
                break
    
    lines.append("__lua__")
    lines.append(from_pico_chars(cart.code))

    lines.append("__gfx__")
    for y in range(128):
        lines.append(nybbles(cart.rom.get4(mem_tile_addr(x, y)) for x in range(128)))
    remove_empty_section_lines()

    lines.append("__map__")
    for y in range(32):
        lines.append(bytes(cart.rom.get8(mem_map_addr(x, y)) for x in range(128)))
    remove_empty_section_lines()

    lines.append("__gff__")
    for y in range(2):
        lines.append(bytes(cart.rom.get8(mem_flag_addr(x, y)) for x in range(128)))
    remove_empty_section_lines() 

    lines.append("__sfx__")
    for y in range(64):
        info = bytes(cart.rom.get8(mem_sfx_info_addr(y, x)) for x in range(4))
        notes = (cart.rom.get16(mem_sfx_addr(y, x)) for x in range(32))
        note_groups = nybble_groups(((n >> 4) & 0x3, n & 0xf, ((n >> 6) & 0x7) | (n >> 12) & 0x8, (n >> 9) & 0x7, (n >> 12) & 0x7) for n in notes)
        lines.append(info + note_groups)
    remove_empty_section_lines()

    lines.append("__music__")
    for y in range(64):
        chans = [cart.rom.get8(mem_music_addr(y, x)) for x in range(4)]
        flags = bytes((sum(((ch >> 7) & 1) << i for i, ch in enumerate(chans)),))
        ids = bytes(ch & 0x7f for ch in chans)
        lines.append(flags + " " + ids)
    remove_empty_section_lines(num_spaces=1)
    
    if cart.screenshot:
        lines.append("__label__")
        for y in range(128):
            lines.append(ext_nybbles(cart.screenshot[x, y] for x in range(128)))
        remove_empty_section_lines()
    
    for meta, metalines in cart.meta.items():
        lines.append("__%s__" % (k_meta_prefix + meta))
        lines += metalines

    return "\n".join(lines)

def iter_rect(width, height):
    for y in range(height):
        for x in range(width):
            yield x, y

k_base64_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + "_-"
k_base64_alt_chars = k_base64_chars[62:].encode()
k_base64_char_map = {ch: i for i, ch in enumerate(k_base64_chars)}

def print_url_size(size, prefix=""):
    print_size(prefix + "url:", size, 2000)

def read_cart_from_url(url, print_sizes=False, **opts):
    if print_sizes:
        print_url_size(len(url), "input ")

    params = re.search("\?c=([^&]*)\&g=([^&]*)", url)
    if not params:
        raise Exception("Invalid url")

    cart = Cart()            
    code, gfx = params.groups()

    codebuf = base64.b64decode(code, k_base64_alt_chars, validate=True).ljust(k_code_size, b'\0')
    with BinaryReader(BytesIO(codebuf), big_end = True) as r:
        cart.code = read_code_from_rom(r, **opts)

    i = 0
    rect = iter_rect(128, 128)
    while i < len(gfx):
        val = k_base64_char_map[gfx[i]]
        i += 1

        color = val & 0xf
        count = (val >> 4) + 1
        if count == 4:
            count += k_base64_char_map[gfx[i]]
            i += 1

        for _ in range(count):
            x, y = next(rect)
            cart.rom.set4(mem_tile_addr(x, y), color)

    return cart

k_url_prefix = "https://www.pico-8-edu.com"

def write_cart_to_url(cart, url_prefix=k_url_prefix, force_compress=False, print_sizes=False, **opts):
    io = BytesIO()
    with BinaryWriter(io, big_end = True) as w:
        write_code_to_rom(w, cart.code, force_compress=True, **opts)

        if len(io.getvalue()) > len(cart.code):
            io = BytesIO(bytes(ord(c) for c in cart.code))

        code = base64.b64encode(io.getvalue(), k_base64_alt_chars)

    rect = iter_rect(128, 128)
    gfx = []
    x, y = next(rect)
    done = False
    while not done:
        color = cart.rom.get4(mem_tile_addr(x, y))
        total_count = 1
        for x, y in rect:
            next_color = cart.rom.get4(mem_tile_addr(x, y))
            if next_color == color:
                total_count += 1
            else:
                break
        else:
            done = True
            if color == 0:
                total_count = 0 if gfx else 1

        while total_count > 0:
            count = min(total_count, 63 + 4)
            total_count -= count

            val = (min(count - 1, 3) << 4) | color
            gfx.append(k_base64_chars[val])

            if count >= 4:
                gfx.append(k_base64_chars[count - 4])

    url = "%s/?c=%s&g=%s" % (url_prefix, code.decode(), "".join(gfx))
    if print_sizes:
        print_url_size(len(url))
    return url

def read_cart_from_export(data, name, **opts):
    data = data.decode()
    cartnames_raw = re.search("var\s+_cartname\s*=\s*\[(.*?)\]", data, re.S)
    assert cartnames_raw
    
    cartnames = {}
    for i, cartname in enumerate(cartnames_raw.group(1).split(",")):
        cartname = cartname.strip()[1:-1]
        cartnames[cartname] = i
    
    cartpos = cartnames.get(name, cartnames.get(path_basename(name)))
    assert cartpos is not None
    
    cartdata_raw = re.search("var\s+_cartdat\s*=\s*\[(.*?)\]", data, re.S)
    assert cartdata_raw
    
    cartsize = k_cart_size
    cartdata = bytearray(k_rom_size)
    for i, b in enumerate(cartdata_raw.group(1).split(",")[cartpos*cartsize : (cartpos+1)*cartsize]):
        cartdata[i] = int(b.strip())
    
    return read_cart_from_rom(cartdata, path=name, **opts)

def read_cart_from_clip(clip, **opts):
    clip = clip.strip()
    prefix, suffix = "[cart]", "[/cart]"
    if clip.startswith(prefix) and clip.endswith(suffix):
        data = bytes.fromhex(clip[len(prefix):-len(suffix)])
        return read_cart_from_image(data, **opts)
    else:
        raise Exception("Invalid clipboard tag")

def write_cart_to_clip(cart, **opts):
    data = write_cart_to_image(cart, **opts)
    return "[cart]%s[/cart]" % data.hex()

def read_cart_autodetect(path, **opts):
    try:
        text = file_read_text(path)

        # cart?
        if text.startswith("pico-8 cartridge") or text.startswith("__lua__"):
            return read_cart_from_source(text, path=path, **opts)
            
        # clip?
        if text.startswith("[cart]"):
            return read_cart_from_clip(text, path=path, **opts)

        # url?
        if text.startswith(k_url_prefix):
            return read_cart_from_url(text, path=path, **opts)

        # plain text?
        return read_cart_from_source(text, raw=True, path=path, **opts)
        
    except UnicodeDecodeError: # required to happen for pngs
        return read_cart(path, CartFormat.png, **opts)

def read_cart(path, format=None, **opts):
    if format in (CartFormat.p8, CartFormat.code):
        return read_cart_from_source(file_read_text(path), path=path, **opts)
    elif format == CartFormat.png:
        return read_cart_from_image(file_read(path), path=path, **opts)
    elif format == CartFormat.rom:
        return read_cart_from_rom(file_read(path), path=path, **opts)
    elif format == CartFormat.clip:
        return read_cart_from_clip(file_read_text(path), path=path, **opts)
    elif format == CartFormat.url:
        return read_cart_from_url(file_read_text(path), path=path, **opts)
    elif format == CartFormat.lua:
        return read_cart_from_source(file_read_text(path), raw=True, path=path, **opts)
    elif format in (None, CartFormat.auto):
        return read_cart_autodetect(path, **opts)
    else:
        fail("invalid read format: %s" % format)

def read_included_cart(orig_path, inc_name, out_i, outparts, outmappings, preprocessor):
    inc_path = path_join(path_dirname(orig_path), inc_name)
    if not path_exists(inc_path):
        raise Exception("cannot open included cart at: %s" % inc_path)

    inc_cart = read_cart(inc_path, preprocessor=preprocessor)
    if inc_cart.code_map:
        for map in inc_cart.code_map:
            outmappings.append(CodeMapping(out_i + map.idx, map.src_name, map.src_code, map.src_idx, map.src_line))
    else:
        outmappings.append(CodeMapping(out_i, inc_name, inc_cart.code, 0, 0))
    outparts.append(inc_cart.code)

    return out_i + len(inc_cart.code)

@staticclass
class PicoPreprocessor:
    strict = True

    def start(path, code):
        pass

    def handle(path, code, i, start_i, out_i, outparts, outmappings):
        end_i = code.find("\n", i)
        end_i = end_i if end_i >= 0 else len(code)

        args = code[i:end_i].split(maxsplit=1)
        if len(args) == 2 and args[0] == "#include":
            out_i = read_included_cart(path, args[1], out_i, outparts, outmappings, PicoPreprocessor)
            return True, end_i, end_i, out_i
        else:
            return True, i + 1, start_i, out_i

    def handle_inline(path, code, i, start_i, out_i, outparts, outmappings):
        return True, i + 1, start_i, out_i
        
    def finish(path, code):
        pass

k_long_brackets_re = re.compile(r"\[(=*)\[(.*?)\]\1\]", re.S)
k_wspace = " \t\r\n"

def preprocess_code(name, path, code, start_line=0, preprocessor=None):
    outparts = []
    outmappings = []
    i = start_i = out_i = 0
    active = True
    
    if preprocessor is None:
        preprocessor = PicoPreprocessor
    preprocessor.start(path, code)

    def skip_long_brackets():
        nonlocal i
        m = k_long_brackets_re.match(code, i)
        if m:
            i = m.end()
            return True

    def flush_output():
        nonlocal start_i, out_i
        if i > start_i and active:
            outparts.append(code[start_i:i])
            outmappings.append(CodeMapping(out_i, name, code, start_i, start_line))
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

        elif list_get(code, i + 1) == '[' and list_get(code, i + 2) != '[': # #[...] inline directive
            flush_output()
            active, i, start_i, out_i = preprocessor.handle_inline(path, code, i, start_i, out_i, outparts, outmappings)

        elif list_get(code, i + 1, '') not in k_wspace: # normal directive?
            hash_i = i
            while list_get(code, i - 1, '') in k_wspace:
                if i == 0 or code[i - 1] == '\n':
                    break
                i -= 1
            else:
                i = hash_i + 1
                continue

            flush_output()
            active, i, start_i, out_i = preprocessor.handle(path, code, hash_i, start_i, out_i, outparts, outmappings)

        else:
            i += 1

    flush_output()
    preprocessor.finish(path, code)
    return "".join(outparts), outmappings

def write_cart(path, cart, format, **opts):
    if format == CartFormat.p8:
        file_write_text(path, write_cart_to_source(cart, **opts))
    elif format == CartFormat.png:
        file_write(path, write_cart_to_image(cart, **opts))
    elif format == CartFormat.rom:
        file_write(path, write_cart_to_rom(cart, **opts))
    elif format == CartFormat.clip:
        file_write_text(path, write_cart_to_clip(cart, **opts))
    elif format == CartFormat.url:
        file_write_text(path, write_cart_to_url(cart, **opts))
    elif format == CartFormat.lua:
        file_write_text(path, from_pico_chars(cart.code))
    elif format == CartFormat.code:
        file_write_text(path, "__lua__\n" + from_pico_chars(cart.code))
    else:
        fail("invalid write format: %s" % format)

