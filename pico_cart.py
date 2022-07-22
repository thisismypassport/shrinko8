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

def read_code(r):
    start_pos = r.pos()
    header = r.bytes(4)
    if header == k_new_compressed_code_header:
        
        unc_size = r.u16()
        com_size = r.u16()
        
        table = [chr(i) for i in range(256)]
        br = BinaryBitReader(r.f)
        
        code = []
        while len(code) < unc_size:
            if br.bit():
                extra = 0
                while br.bit():
                    extra += 1
                idx = br.bits(4 + extra) + make_mask(4, extra)
                
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
                
                else:
                    count = 3
                    while True:
                        part = br.bits(3)
                        count += part
                        if part != 7:
                            break
                    
                    for _ in range(count):
                        code.append(code[-offset])
        
        assert r.pos() == start_pos + com_size
        assert len(code) == unc_size
        return "".join(code)

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

        assert len(code) in (unc_size, unc_size - 1) # extra null at the end dropped?
        return "".join(code)

    else:
        r.addpos(-4)
        return "".join(chr(c) for c in r.zbytes())

def read_cart_raw(f):
    cart = Cart()
    
    with BinaryReader(f, big_end = True) as r:
        cart.rom.replace(r.bytes(k_rom_size))
        cart.code = read_code(r)

        r.setpos(k_memory_size)
        cart.version = r.u8()
        cart.date = r.u32()

    return cart

def read_cart_from_rom(buffer):
    return read_cart_raw(BytesIO(buffer))

def get_lz77(code, prev_code=None, min_c=3, max_c=0x7fff, max_o=0x7fff):    
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
    items = []
    while i < len(code):
        best_c, best_j = find_match(i)

        if best_c >= 0 and i + 1 < len(code):
            best_cp1, best_jp1 = find_match(i+1)
            if best_cp1 > best_c:
                items.append(code[i])
                i += 1
                best_c, best_j = best_cp1, best_jp1

        if best_c >= 0:
            offset_val = i - best_j - 1
            count_val = best_c - min_c
            items.append(Dynamic(off=offset_val, cnt=count_val))
            i += best_c
        else:
            items.append(code[i])
            i += 1
            
        for j in range(prev_i, i):
            min_matches[code[j:j+min_c]].append(j)
        prev_i = i

    return items

def write_code(w, code):
    k_new = True
    
    print("code:", len(code), str(int(len(code) / 0xffff * 100)) + "%")

    if len(code) >= k_code_size: # (>= due to null)
        start_pos = w.pos()
        w.bytes(k_new_compressed_code_header if k_new else k_compressed_code_header)
        w.u16(len(code))
        len_pos = w.pos()
        w.u16(0) # revised below
                
        if k_new:
            bw = BinaryBitWriter(w.f)
            mtf = [chr(i) for i in range(0x100)]

        items = get_lz77(code, max_c=None if k_new else 0x11, max_o=0x7fff if k_new else 0xc3f)

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
                
                for ii in range(ch_i, 0, -1):
                    mtf[ii] = mtf[ii - 1]
                mtf[0] = ch 
                
            else:
                ch_i = k_inv_code_table.get(ch, 0)
                
                if ch_i > 0:
                    w.u8(ch_i)
                
                else:
                    w.u8(0)
                    w.u8(ord(ch))

        for item in items:
            if isinstance(item, Dynamic):
                write_match(item.off, item.cnt)
            else:
                write_literal(item)
                
        if k_new:
            bw.flush()

        size = w.pos() - start_pos
        print("space:", size, str(int(size / k_code_size * 100)) + "%")
        assert w.pos() <= k_memory_size
        
        if k_new:   
            w.setpos(len_pos)
            w.u16(size)
            
    else:
        w.bytes(bytes(ord(c) for c in code))

def write_cart_to_rom(cart):
    output = BytesIO(bytearray(k_memory_size + 0x20))
    
    w = BinaryWriter(output, big_end = True)
    
    w.bytes(cart.rom.get_block(0, k_rom_size))
    
    write_code(w, cart.code)
            
    w.setpos(k_memory_size)
    w.u8(cart.version)
    w.u32(cart.date)

    return output.getbuffer()

k_cart_image_width, k_cart_image_height = 160, 205

def load_cart_image(f):
    r = BinaryReader(f)
    if r.bytes(8) != b"\x89PNG\r\n\x1a\n":
        raise WrongFileTypeError()
    r.subpos(8)

    image = Surface.load(f)
    if image.width != k_cart_image_width or image.height != k_cart_image_height:
        raise WrongFileTypeError()

    return image

def read_cart_from_image(f):
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

    return read_cart_raw(BytesIO(data))
    
def write_cart_to_image(f, cart, res_path, screenshot_path=None, title=None):
    output = write_cart_to_rom(cart)
    
    with file_open(path_join(res_path, "template.png")) as template_f:
        image = load_cart_image(template_f)
        width, height = image.size

        if screenshot_path:
            with file_open(screenshot_path) as screenshot_f:
                screenshot_surf = Surface.load(screenshot_f)
                screenshot_surf.blend_mode = BlendMode.none
                image.draw(screenshot_surf, Point(16, 24), Rect(0, 0, 128, 128))
        
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
                    image.draw(font_surf, Point(18, 167) + Point(x, y), chrect)
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
    
    lines.append("__lua__")
    for line in cart.code.splitlines():
        lines.append(from_pico_chars(line))

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

    return "\n".join(lines)
        
def read_cart_from_text(f):
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

    return read_cart_from_stream(BytesIO(data))

def read_cart_from_stream(f):
    try:
        pos = f.tell()
        return read_cart_from_text(f)
    except WrongFileTypeError:
        f.seek(pos)
        return read_cart_from_image(f)

def read_cart_from_export(data, name):
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
    
    return read_cart_from_rom(cartdata)

def read_cart(path):
    try:
        with file_open(path) as f:
            return read_cart_from_stream(f)
    except IOError:
        name = None
        while not path_exists(path):
            path, namepart = path_split_name(path)
            name = namepart if name is None else namepart + "/" + name
        with file_open(path) as f:
            return read_cart_from_export(f.read(), name)
