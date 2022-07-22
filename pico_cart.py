from utils import *
from sdl2_utils import Surface, BlendMode
from pico_defs import *

k_latest_version = 35
k_latest_date = 132215

class Cart:
    def __init__(m):
        m.version = k_latest_version
        m.date = k_latest_date
        m.rom = Memory(k_rom_size)
        m.code = ""
        m.screenshot = None
        m.meta = defaultdict(list)

    def get_title(m):
        title = m.meta.get("title")
        if title is None:
            title = []
            for line in m.code.splitlines()[:2]:
                if line.startswith("--"):
                    title.append(line[2:].strip())
        return title

class WrongFileTypeError(Exception):
    pass

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

def read_code(r, print_sizes=False):
    start_pos = r.pos()
    header = r.bytes(4)

    if header == k_new_compressed_code_header:
        unc_size = r.u16()
        com_size = r.u16()

        if print_sizes:
            print_compressed_size(com_size, "input ")
        
        table = [chr(i) for i in range(256)]
        br = BinaryBitReader(r.f)
        
        code = []
        while len(code) < unc_size:
            #last_bit_pos = br.bit_position
            if br.bit():
                extra = 0
                while br.bit():
                    extra += 1
                idx = br.bits(4 + extra) + make_mask(4, extra)
                
                #print(len(code), ord(table[idx]), br.bit_position - last_bit_pos)
                code.append(table[idx])
                
                for i in range(idx, 0, -1):
                    table[i] = table[i - 1]
                table[0] = code[-1]
            else:
                offlen = (5 if br.bit() else 10) if br.bit() else 15                
                offset = br.bits(offlen) + 1

                if offset == 1 and offlen != 5:
                    assert offlen == 10
                    while len(code) < unc_size: # or True?
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
        code = [chr(c) for c in r.zbytes()]

    if print_sizes:
        print_code_size(len(code), "input ")    
    
    return "".join(code)

def read_cart_raw(f, **opts):
    cart = Cart()
    
    with BinaryReader(f, big_end = True) as r:
        cart.rom.replace(r.bytes(k_rom_size))
        cart.code = read_code(r, **opts)

        r.setpos(k_memory_size)
        cart.version = r.u8()
        cart.date = r.u32()

    return cart

def read_cart_from_rom(buffer, **opts):
    return read_cart_raw(BytesIO(buffer), **opts)

class Lz77Tuple(Tuple):
    fields = ("off", "cnt")

def get_lz77(code, prev_code=None, min_c=3, max_c=0x7fff, max_o=0x7fff, measure_c=None, measure=None):
    min_matches = defaultdict(list)

    if prev_code:
        for i in range(len(prev_code) - min_c + 1):
            min_matches[prev_code[i:i+min_c]].append(i - len(prev_code))

    def get_match_length(left, left_i, right, right_i):
        c = 0
        limit = min(len(left) - left_i, len(right) - right_i)
        while left[left_i + c] == right[right_i + c]:
            c += 1
            if c >= limit:
                break
        return c

    def find_match(i):
        best_c = -1
        best_j = -1
        for j in min_matches[code[i:i+min_c]]:
            if e(max_o) and j < i - max_o:
                continue

            if j < 0:
                c = get_match_length(code, i, prev_code, j + len(prev_code))
            else:
                c = get_match_length(code, i, code, j)

            if e(max_c):
                c = min(c, max_c)

            if c > best_c and c >= min_c or c == best_c and j > best_j:
                best_c = c
                best_j = j
        
        return best_c, best_j

    i = 0
    prev_i = 0
    while i < len(code):
        best_c, best_j = find_match(i)

        if best_c >= 0 and measure and best_c <= measure_c:
            lz_cost = measure(Lz77Tuple(i - best_j - 1, best_c - min_c))
            ch_cost = measure(code[i:i+best_c])
            if ch_cost < lz_cost:
                best_c = -1

        if best_c >= 0 and i + 1 < len(code):
            best_cp1, best_jp1 = find_match(i+1)
            if measure and best_cp1 in (best_c, best_c - 1):
                lz_cost = measure(Lz77Tuple(i - best_j - 1, best_c - min_c)) + (measure(code[best_j:best_j+1]) if best_cp1 == best_c else 0)
                p1_cost = measure(code[i:i+1]) + measure(Lz77Tuple(i - best_jp1, best_cp1 - min_c))
                #print(p1_cost, "vs.", lz_cost)
                if p1_cost < lz_cost:
                    best_c = -1

            """if measure:
                best_cp2, best_jp2 = find_match(i+2)
                if best_cp2 > best_cp1 + 1 and best_cp2 > best_c + 1:
                    lz_cost = 
                    p2_cost = measure(code[i:i+2]) + measure(Lz77Tuple(i - best_jp2))

                    yield code[i]
                    yield code[i+1]
                    i += 2
                    best_c, best_j = best_cp2, best_jp2"""

            if best_cp1 > best_c:
                yield code[i]
                i += 1
                best_c, best_j = best_cp1, best_jp1

        if best_c >= 0:
            yield Lz77Tuple(i - best_j - 1, best_c - min_c)
            i += best_c
        else:
            yield code[i]
            i += 1
            
        for j in range(prev_i, i):
            min_matches[code[j:j+min_c]].append(j)
        prev_i = i

def print_code_size(size, prefix=""):
    print(prefix + "chars:", size, str(int(size / 0xffff * 100)) + "%")

def print_compressed_size(size, prefix=""):
    print(prefix + "compressed:", size, str(int(size / k_code_size * 100)) + "%")

def write_code(w, code, print_sizes=True, force_compress=False, fail_on_error=True):
    k_new = True
    
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

            def update_mtf(mtf, idx, ch):
                for ii in range(idx, 0, -1):
                    mtf[ii] = mtf[ii - 1]
                mtf[0] = ch
            
            def measure(items):
                if isinstance(items, Lz77Tuple):
                    offset_bits = max(round_up(count_significant_bits(items.off), 5), 5)
                    count_bits = ((items.cnt // 7) + 1) * 3
                    return 2 + (offset_bits < 15) + offset_bits + count_bits

                else:
                    mtfcopy = mtf[:]
                    count = 0
                    for item in items:
                        ch_i = mtfcopy.index(item)

                        mask = 1 << 4
                        large = False
                        while ch_i >= mask:
                            mask = (mask << 1) | (1 << 4)
                            count += 2
                            large = True
                        count += 4 if large else 6 # large is a heuristic since mtf usually pays forward

                        update_mtf(mtfcopy, ch_i, item)                        
                    return count

            measure_c = 3
        else:
            measure = measure_c = None

        def write_match(offset_val, count_val):
            if k_new:
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
                
            else:
                offset_val += 1
                count_val += 1
                w.u8(0x3c + (offset_val >> 4))
                w.u8((offset_val & 0xf) + (count_val << 4))

        def write_literal(ch):
            if k_new:
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
                
            else:
                ch_i = k_inv_code_table.get(ch, 0)
                
                if ch_i > 0:
                    w.u8(ch_i)
                
                else:
                    w.u8(0)
                    w.u8(ord(ch))

        #dbg_size = 0
        for item in get_lz77(code, max_c=None if k_new else 0x11, max_o=0x7fff if k_new else 0xc3f, measure=measure, measure_c=measure_c):
            last_bit_pos = bw.bit_position
            if isinstance(item, Lz77Tuple):
                write_match(item.off, item.cnt)
                #print(dbg_size, "%s:%s" % (item.off, item.cnt), bw.bit_position - last_bit_pos)
                #dbg_size += item.cnt + 3
            else:
                write_literal(item)
                #print(dbg_size, ord(item), bw.bit_position - last_bit_pos)
                #dbg_size += 1
                
        if k_new:
            bw.flush()

        size = w.pos() - start_pos
        if print_sizes:
            print_compressed_size(size)
        
        if fail_on_error:
            assert len(code) < 0x10000
            assert w.pos() <= k_memory_size
        
        if k_new:   
            w.setpos(len_pos)
            w.u16(size)
            
    else:
        w.bytes(bytes(ord(c) for c in code))

def write_code_sizes(code):
    write_code(BinaryWriter(BytesIO()), code, force_compress=True, fail_on_error=False)

def write_cart_to_rom(cart, **opts):
    output = BytesIO(bytearray(k_memory_size + 0x20))
    
    w = BinaryWriter(output, big_end = True)
    
    w.bytes(cart.rom.get_block(0, k_rom_size))
    
    write_code(w, cart.code, **opts)
            
    w.setpos(k_memory_size)
    w.u8(cart.version)
    w.u32(cart.date)

    return output.getbuffer()

k_cart_image_width, k_cart_image_height = 160, 205
k_screenshot_rect = Rect(0, 0, 128, 128)
k_screenshot_offset = Point(16, 24)
k_title_offset = Point(18, 167)

def load_cart_image(f):
    r = BinaryReader(f)
    if r.bytes(8) != b"\x89PNG\r\n\x1a\n":
        raise WrongFileTypeError()
    r.subpos(8)

    image = Surface.load(f)
    if image.width != k_cart_image_width or image.height != k_cart_image_height:
        raise WrongFileTypeError()

    return image

def read_cart_from_image(f, **opts):
    image = load_cart_image(f)
    width, height = image.size

    data = bytearray()
    image.lock()
    for y in range(height):
        for x in range(width):
            r, g, b, a = image.get_at((x,y))
            byte = ((b & 3) << 0) | ((g & 3) << 2) | ((r & 3) << 4) | ((a & 3) << 6)
            data.append(byte)
    image.unlock()

    return read_cart_raw(BytesIO(data), **opts)
    
def write_cart_to_image(f, cart, res_path, screenshot_path=None, title=None, **opts):
    output = write_cart_to_rom(cart, **opts)
    
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

        image.save(f)

k_meta_prefix = "meta:"
        
def read_cart_from_source(data):
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
    
    header = None
    code = []
    y = 0
    for line in data.splitlines():
        clean = line.strip()
            
        if line.startswith("__") and line.endswith("__"):
            header = line[2:-2]
            y = 0
            
        elif header == "lua":
            code.append(to_pico_chars(line))
            code.append("\n")
            
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
            cart.meta[header[len(k_meta_prefix):]].append(line)
            
        elif header == None and clean.startswith("version "):
            cart.version = int(clean.split()[1])
            
    cart.code = "".join(code)
    return cart

def write_cart_to_source(cart):
    lines = ["pico-8 cartridge // http://www.pico-8.com"]
    lines.append("version %d" % cart.version)

    def nybbles(data):
        return "".join('%01x' % b for b in data)
    
    def nybble_groups(data):
        return "".join([nybbles(group) for group in data])
    
    def bytes(data):
        return "".join('%02x' % b for b in data)

    def ext_nybbles(data):
        return "".join(('%01x' % b if b < 16 else chr(b - 16 + ord('g'))) for b in data)
    
    lines.append("__lua__")
    lines.append(from_pico_chars(cart.code))

    lines.append("__gfx__")
    for y in range(128):
        lines.append(nybbles(cart.rom.get4(mem_tile_addr(x, y)) for x in range(128)))

    lines.append("__map__")
    for y in range(32):
        lines.append(bytes(cart.rom.get8(mem_map_addr(x, y)) for x in range(128)))

    lines.append("__gff__")
    for y in range(2):
        lines.append(bytes(cart.rom.get8(mem_flag_addr(x, y)) for x in range(128)))    

    lines.append("__sfx__")
    for y in range(64):
        info = bytes(cart.rom.get8(mem_sfx_info_addr(y, x)) for x in range(4))
        notes = (cart.rom.get16(mem_sfx_addr(y, x)) for x in range(32))
        note_groups = nybble_groups(((n >> 4) & 0x3, n & 0xf, ((n >> 6) & 0x7) | (n >> 12) & 0x8, (n >> 9) & 0x7, (n >> 12) & 0x7) for n in notes)
        lines.append(info + note_groups)

    lines.append("__music__")
    for y in range(64):
        chans = [cart.rom.get8(mem_music_addr(y, x)) for x in range(4)]
        flags = bytes((sum(((ch >> 7) & 1) << i for i, ch in enumerate(chans)),))
        ids = bytes(ch & 0x7f for ch in chans)
        lines.append(flags + " " + ids)
    
    if cart.screenshot:
        lines.append("__label__")
        for y in range(128):
            lines.append(ext_nybbles(cart.screenshot[x, y] for x in range(128)))
    
    for meta, metalines in cart.meta.items():
        lines.append("__%s__" % (k_meta_prefix + meta))
        lines += metalines

    return "\n".join(lines)
        
def read_cart_from_text(f, **opts):
    try:
        data = f.read().decode()
    except UnicodeDecodeError:
        raise WrongFileTypeError()
    
    # cart?
    if data.startswith("pico-8 cartridge") or data.startswith("__lua__"):
        return read_cart_from_source(data)
        
    # cart block?
    data = data.strip()
    prefix, suffix = "[cart]", "[/cart]"
    if not data.startswith(prefix) or not data.endswith(suffix):
        raise WrongFileTypeError()

    data = data[len(prefix):-len(suffix)]
    data = bytes.fromhex(data)

    return read_cart_from_stream(BytesIO(data), **opts)

def read_cart_from_stream(f, **opts):
    try:
        pos = f.tell()
        return read_cart_from_text(f, **opts)
    except WrongFileTypeError:
        f.seek(pos)
        return read_cart_from_image(f, **opts)

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
    
    cartsize = k_memory_size
    cartdata = bytearray(k_rom_size)
    for i, b in enumerate(cartdata_raw.group(1).split(",")[cartpos*cartsize : (cartpos+1)*cartsize]):
        cartdata[i] = int(b.strip())
    
    return read_cart_from_rom(cartdata, **opts)

def read_cart(path, **opts):
    try:
        with file_open(path) as f:
            return read_cart_from_stream(f, **opts)
    except IOError:
        name = None
        while not path_exists(path):
            path, namepart = path_split_name(path)
            name = namepart if name is None else namepart + "/" + name
        if path_is_file(path):
            with file_open(path) as f:
                return read_cart_from_export(f.read(), name, **opts)
        else:
            raise
