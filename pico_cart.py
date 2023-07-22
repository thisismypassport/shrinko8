from utils import *
from sdl2_utils import Surface, BlendMode, Color
from pico_defs import *
from pico_compress import compress_code, uncompress_code, get_compressed_size, print_size
import hashlib, base64

class CartFormat(Enum):
    """An enum representing the supported cart formats"""
    auto = p8 = png = lua = rom = tiny_rom = clip = url = code = js = pod = ...

CartFormat.input_names = tuple(CartFormat._values.keys())
CartFormat.output_names = tuple(name for name in CartFormat.input_names if name != "auto")
CartFormat.ext_names = tuple(name for name in CartFormat.input_names if name not in ("auto", "tiny_rom", "code"))
CartFormat.src_names = ("p8", "lua", "code")
CartFormat.export_names = ("js", "pod")

class CodeMapping(Tuple):
    """Specifies that code starting at index 'idx' maps to the given source starting at index 'src_idx'"""
    idx = src_path = src_code = src_idx = src_line = ...

class Cart:
    """A pico8 cart, including its code (as a p8str), rom (as a Memory), and more"""

    def __init__(m, code="", rom=None):
        m.version_id = get_default_version_id()
        m.version_tuple = get_version_tuple(m.version_id)
        m.platform = get_default_platform()
        m.rom = rom.copy() if rom else mem_create_rom()
        m.path = ""
        m.code = code
        m.code_map = ()
        m.code_rom = None
        m.screenshot = None
        m.meta = defaultdict(list)

    def copy(m):
        return deepcopy(m)

    @property
    def title(m):
        title_meta = m.meta.get("title")
        if title_meta is None:
            title = ""
            for line in m.code.split("\n", 2)[:2]: # (splitlines isn't appropriate for p8str)
                match = re.fullmatch(r"-- ?(.*)", line)
                if match:
                    title += match.group(1)
                title += "\n"
            return title.rstrip("\n")
        else:
            return "\n".join(to_p8str(line) for line in title_meta)

    @title.setter
    def title(m, value):
        m.meta["title"] = from_p8str(value).splitlines()

    def set_code_without_title(m, code):
        old_title = m.title
        m.code = code
        if old_title != m.title:
            m.title = old_title

def read_code_from_rom(r, keep_compression=False, **opts):
    code_rom = None
    if keep_compression:
        start_pos = r.pos()
        code_rom = Memory(k_code_size)
        code_rom.set_block(0, r.bytes(k_code_size, allow_eof=True))
        r.setpos(start_pos)

    return uncompress_code(r, **opts), code_rom

def read_cart_from_rom(buffer, path=None, allow_tiny=False, **opts):
    cart = Cart()
    cart.path = path
    
    with BinaryReader(BytesIO(buffer), big_end = True) as r:
        if r.len() < k_cart_size and allow_tiny: # tiny rom, code only
            cart.code, cart.code_rom = read_code_from_rom(r, **opts)
        
        else:
            cart.rom.replace(r.bytes(k_rom_size))
            cart.code, cart.code_rom = read_code_from_rom(r, **opts)

            r.setpos(k_cart_size)
            if r.pos() < r.len():
                cart.version_id = r.u8()
                version = r.u8(), r.u8(), r.u8()
                cart.platform = chr(r.u8())
                cart.version_tuple = (*version, r.u8())
                hash = r.bytes(20)

                if hash != bytes(20) and hash != hashlib.sha1(buffer[:k_cart_size]).digest():
                    throw("corrupted cart (wrong hash)")

    return cart

def write_cart_to_rom(cart, with_trailer=False, keep_compression=False, **opts):
    io = BytesIO(bytes(k_cart_size + (k_trailer_size if with_trailer else 0)))

    with BinaryWriter(io, big_end = True) as w:
        w.bytes(cart.rom)

        if keep_compression and cart.code_rom != None:
            w.bytes(cart.code_rom)
        else:
            compress_code(w, cart.code, **opts)

        if with_trailer:
            w.setpos(k_cart_size)
            w.u8(cart.version_id)
            w.u8(cart.version_tuple[0])
            w.u8(cart.version_tuple[1])
            w.u8(cart.version_tuple[2])
            w.u8(ord(cart.platform))
            w.u8(cart.version_tuple[3])
            w.bytes(hashlib.sha1(io.getvalue()[:k_cart_size]).digest())

        return io.getvalue()

def write_cart_to_tiny_rom(cart, force_compress=False, keep_compression=False, **opts):
    io = BytesIO()

    with BinaryWriter(io, big_end = True) as w:
        if keep_compression and cart.code_rom != None:
            with BinaryReader(BytesIO(cart.code_rom), big_end = True) as code_r:
                compressed_size = get_compressed_size(code_r)
            
            w.bytes(cart.code_rom.get_block(0, compressed_size))
        else:
            compress_code(w, cart.code, force_compress=True, **opts)

            if len(io.getvalue()) > len(cart.code):
                io = BytesIO(encode_p8str(cart.code))

        return io.getvalue()

k_cart_image_width, k_cart_image_height = 160, 205
k_screenshot_rect = Rect(0, 0, 128, 128)
k_screenshot_offset = Point(16, 24)
k_title_offset = Point(18, 167)
k_title_spacing = Point(0, 2)
k_title_size = Point(31 * 4, 16)

k_palette_map_6bpp = {Color(c.r & ~3, c.g & ~3, c.b & ~3, c.a & ~3): i for c, i in k_palette_map.items()}

def load_cart_image(f):
    r = BinaryReader(f)
    if r.bytes(8) != b"\x89PNG\r\n\x1a\n":
        throw("Not a valid png")
    r.subpos(8)

    image = Surface.load(f)
    if image.width != k_cart_image_width or image.height != k_cart_image_height:
        throw("Png has wrong size")

    return image

def read_cart_from_image(data, **opts):
    image = load_cart_image(BytesIO(data))
    width, height = image.size

    data = bytearray()
    screenshot = MultidimArray(k_screenshot_rect.size, 0)
    pixels = image.pixels

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            byte = ((b & 3) << 0) | ((g & 3) << 2) | ((r & 3) << 4) | ((a & 3) << 6)
            data.append(byte)

    for y in range(k_screenshot_rect.h):
        for x in range(k_screenshot_rect.w):
            r, g, b, a = pixels[Point(x, y) + k_screenshot_offset]
            screenshot[x, y] = k_palette_map_6bpp.get((r & ~3, g & ~3, b & ~3, a & ~3), 0)

    cart = read_cart_from_rom(data, **opts)
    cart.screenshot = screenshot
    return cart

def get_res_path():
    return path_dirname(path_resolve(__file__))

def draw_text_on_image(image, text, offset, size, spacing=Point.zero, wrap=False):
    with file_open(path_join(get_res_path(), "font.png")) as font_f:
        font_surf = Surface.load(font_f)
        x, y = 0, 0
        for ch in text:
            chi = ord(ch)
            chrect = Rect(chi % 16 * 8, chi // 16 * 6, 8 if chi >= 0x80 else 4, 6)
            new_x = x + chrect.w + spacing.x
            if ch == '\n' or (wrap and new_x > size.x):
                new_x -= x
                x = 0
                y += chrect.h + spacing.y
                if y >= size.y:
                    break
                elif ch == '\n':
                    continue
            if new_x <= size.x:
                image.draw(font_surf, offset + Point(x, y), chrect)
            x = new_x

def create_screenshot_surface(screenshot):
    screenshot_surf = Surface.create(*k_screenshot_rect.size)
    screenshot_pixels = screenshot_surf.pixels
    for y in range(k_screenshot_rect.h):
        for x in range(k_screenshot_rect.w):
            screenshot_pixels[x, y] = k_palette[screenshot[x, y]]
    return screenshot_surf

def write_cart_to_image(cart, screenshot_path=None, title=None, **opts):
    output = write_cart_to_rom(cart, with_trailer=True, **opts)

    with file_open(path_join(get_res_path(), "template.png")) as template_f:
        image = load_cart_image(template_f)
        width, height = image.size

        if screenshot_path:
            with file_open(screenshot_path) as screenshot_f:
                screenshot_surf = Surface.load(screenshot_f)
                screenshot_surf.blend_mode = BlendMode.none
                image.draw(screenshot_surf, k_screenshot_offset, k_screenshot_rect)
        
        elif cart.screenshot:
            screenshot_surf = create_screenshot_surface(cart.screenshot)
            image.draw(screenshot_surf, k_screenshot_offset, k_screenshot_rect)
        
        wrap = True
        if title is None:
            title = cart.title
            wrap = False
        if title:
            draw_text_on_image(image, title, k_title_offset, k_title_size, k_title_spacing, wrap=wrap)
        
        pixels = image.pixels

        for y in range(height):
            for x in range(width):
                i = x + y * width
                byte = output[i]
                r, g, b, a = pixels[x,y]
                b = (b & ~3) | (byte & 3)
                g = (g & ~3) | ((byte >> 2) & 3)
                r = (r & ~3) | ((byte >> 4) & 3)
                a = (a & ~3) | ((byte >> 6) & 3)
                pixels[x, y] = (r, g, b, a)

        f = BytesIO()
        image.save(f)
        return f.getvalue()

k_p8_prefix = "pico-8 cartridge"
k_meta_prefix = "meta:"

def read_cart_from_source(data, path=None, raw=False, preprocessor=None, **_):
    cart = Cart()
    cart.path = path
    
    def nybbles(line):
        for b in line:
            yield int(b, 16)
    
    def nybble_groups(line, n):
        for i in range(0, len(line), n):
            yield nybbles(line[i:i+n].ljust(n, "0"))
    
    def bytes(line):
        for i in range(0, len(line), 2):
            yield int(line[i:i+2].ljust(2, "0"), 16)
    
    def ext_nybbles(line):
        for b in line:
            if 'v' >= b.lower() >= 'g':
                yield ord(b.lower()) - ord('g') + 16
            else:
                yield int(b, 16)
      
    if not raw and not data.startswith(k_p8_prefix) and not data.startswith("__lua__"): # fallback to raw
        raw = True
    
    header = "lua" if raw else None
    code = []
    code_line = 0
    y = 0
    for line_i, line in enumerate(data.split("\n")): # not splitlines, that eats a trailing empty line
        try:
            clean = line.strip()
            
            if line.startswith("__") and clean.endswith("__") and not raw: # may end with whitespace
                header = clean[2:-2]
                y = 0
                
            elif header == "lua":
                if y == 0:
                    code_line = line_i
                else:
                    code.append("\n")
                code.append(to_p8str(line))
                y += 1
                
            elif header == "gfx" and clean and y < 0x80:
                x = 0
                for b in nybbles(clean):
                    if x < 0x80:
                        cart.rom.set4(mem_tile_addr(x, y), b)
                        x += 1
                y += 1
                    
            elif header == "map" and clean and y < 0x40: # usually 0x20
                x = 0
                for b in bytes(clean):
                    if x < 0x80:
                        cart.rom.set8(mem_map_addr(x, y), b)
                        x += 1
                y += 1
                    
            elif header == "gff" and clean and y < 2:
                x = 0
                for b in bytes(clean):
                    if x < 0x80:
                        cart.rom.set8(mem_flag_addr(x, y), b)
                        x += 1
                y += 1
                
            elif header == "sfx" and clean and y < 0x40:
                x = 0
                for b in bytes(clean[:8]):
                    cart.rom.set8(mem_sfx_info_addr(y, x), b)
                    x += 1
                x = 0
                for bph, bpl, bw, bv, be in nybble_groups(clean[8:], 5):
                    if x < 0x20:
                        value = bpl | ((bph & 0x3) << 4) | ((bw & 0x7) << 6) | ((bv & 0x7) << 9) | ((be & 0x7) << 12) | ((bw & 0x8) << 12) 
                        cart.rom.set16(mem_sfx_addr(y, x), value)
                        x += 1
                y += 1
                
            elif header == "music" and clean and y < 0x40:
                x = 0
                flags = next(bytes(clean[:2]))
                for b in bytes(clean[3:]):
                    if x < 4:
                        value = b | (((flags >> x) & 1) << 7) 
                        cart.rom.set8(mem_music_addr(y, x), value)
                        x += 1
                y += 1

            elif header == "label" and clean and y < 0x80:
                if cart.screenshot is None:
                    cart.screenshot = MultidimArray(k_screenshot_rect.size, 0)
                x = 0
                for b in ext_nybbles(clean):
                    if x < 0x80:
                        cart.screenshot[x, y] = b
                        x += 1
                y += 1

            elif header and header.startswith(k_meta_prefix):
                cart.meta[header[len(k_meta_prefix):]].append(line.rstrip('\n'))
                
            elif header == None and clean.startswith("version "):
                cart.version_id = int(clean.split()[1])
                cart.version_tuple = get_version_tuple(cart.version_id)

        except Exception as e:
            throw(f"Invalid {header} line in p8 file (line #{line_i + 1})")
            
    cart.code, cart.code_map = preprocess_code(path, "".join(code), code_line, preprocessor=preprocessor)
    return cart

def write_cart_to_source(cart, unicode_caps=False, **_):
    lines = [k_p8_prefix + " // http://www.pico-8.com"]
    lines.append(f"version {cart.version_id}")
    defrom = mem_create_rom()

    def nybbles(data):
        return "".join('%01x' % b for b in data)
    
    def nybble_groups(data):
        return "".join([nybbles(group) for group in data])
    
    def bytes(data):
        return "".join('%02x' % b for b in data)

    def ext_nybbles(data):
        return "".join(('%01x' % b if b < 16 else chr(b - 16 + ord('g'))) for b in data)

    def get_needed_lines(max_lines, addr_func, size):
        lines = max_lines
        for y in reversed(range(max_lines)):
            if cart.rom.cmpeqwith8(addr_func(y), size, defrom):
                lines -= 1
            else:
                break
        return lines

    lines.append("__lua__")
    lines.append(from_p8str(cart.code, unicaps=unicode_caps))

    gfx_lines = get_needed_lines(0x80, lambda y: mem_tile_addr(0, y)[0], 0x40)
    if gfx_lines:
        lines.append("__gfx__")
        for y in range(gfx_lines):
            lines.append(nybbles(cart.rom.get4(mem_tile_addr(x, y)) for x in range(128)))

    map_lines = get_needed_lines(0x20, lambda y: mem_map_addr(0, y), 0x80)
    if map_lines:
        lines.append("__map__")
        for y in range(map_lines):
            lines.append(bytes(cart.rom.get8(mem_map_addr(x, y)) for x in range(128)))

    gff_lines = get_needed_lines(2, lambda y: mem_flag_addr(0, y), 0x80)
    if gff_lines:
        lines.append("__gff__")
        for y in range(gff_lines):
            lines.append(bytes(cart.rom.get8(mem_flag_addr(x, y)) for x in range(128)))

    sfx_lines = get_needed_lines(0x40, lambda y: mem_sfx_addr(y, 0), 0x44)
    if sfx_lines:
        lines.append("__sfx__")
        for y in range(sfx_lines):
            info = bytes(cart.rom.get8(mem_sfx_info_addr(y, x)) for x in range(4))
            notes = (cart.rom.get16(mem_sfx_addr(y, x)) for x in range(32))
            note_groups = nybble_groups(((n >> 4) & 0x3, n & 0xf, ((n >> 6) & 0x7) | (n >> 12) & 0x8, (n >> 9) & 0x7, (n >> 12) & 0x7) for n in notes)
            lines.append(info + note_groups)

    music_lines = get_needed_lines(0x40, lambda y: mem_music_addr(y, 0), 0x4)
    if music_lines:
        lines.append("__music__")
        for y in range(music_lines):
            chans = [cart.rom.get8(mem_music_addr(y, x)) for x in range(4)]
            flags = bytes((sum(((ch >> 7) & 1) << i for i, ch in enumerate(chans)),))
            ids = bytes(ch & 0x7f for ch in chans)
            lines.append(flags + " " + ids)
    
    if cart.screenshot and any(cart.screenshot.array):
        lines.append("__label__")
        for y in range(128):
            lines.append(ext_nybbles(cart.screenshot[x, y] for x in range(128)))
    
    for meta, metalines in cart.meta.items():
        lines.append(f"__{k_meta_prefix + meta}__")
        lines += metalines

    return "\n".join(lines)

def write_cart_to_raw_source(cart, with_header=False, unicode_caps=False, **_):
    source = from_p8str(cart.code, unicaps=unicode_caps)
    if with_header:
        source = "__lua__\n" + source
    return source

def iter_rect(width, height):
    for y in range(height):
        for x in range(width):
            yield x, y

k_base64_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + "_-"
k_base64_alt_chars = k_base64_chars[62:].encode()
k_base64_char_map = {ch: i for i, ch in enumerate(k_base64_chars)}

def print_url_size(size, **kwargs):
    print_size("url", size - k_url_prefix_size, k_url_size, **kwargs)

def read_cart_from_url(url, size_handler=None, **opts):
    if size_handler:
        print_url_size(len(url), prefix="input", handler=size_handler)

    if "?" not in url:
        throw("Invalid url - no '?'")

    code, gfx = None, None
    
    url_params = url.split("?", 1)[1]
    for url_param in url_params.split("&"):
        if "=" not in url_param:
            throw(f"Invalid url param: {url_param}")
        
        key, value = url_param.split("=", 1)
        if key == "c":
            code = value
        elif key == "g":
            gfx = value
        else:
            throw(f"Unknown url param: {key}")

    cart = Cart()

    if code:
        codebuf = base64.b64decode(code, k_base64_alt_chars, validate=True).ljust(k_code_size, b'\0')
        with BinaryReader(BytesIO(codebuf), big_end = True) as r:
            cart.code, cart.code_rom = read_code_from_rom(r, **opts)

    if gfx:
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

def write_cart_to_url(cart, url_prefix=k_url_prefix, force_compress=False, size_handler=None, **opts):
    raw_code = write_cart_to_tiny_rom(cart, **opts)        
    code = base64.b64encode(raw_code, k_base64_alt_chars)

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
                total_count = 0

        while total_count > 0:
            count = min(total_count, 63 + 4)
            total_count -= count

            val = (min(count - 1, 3) << 4) | color
            gfx.append(k_base64_chars[val])

            if count >= 4:
                gfx.append(k_base64_chars[count - 4])

    url = url_prefix
    url += "/?c=" + code.decode()
    if gfx:
        url += "&g=" + "".join(gfx)
    
    if size_handler:
        print_url_size(len(url), handler=size_handler)
        
    check(len(url) - k_url_prefix_size <= k_url_size, "url has too many characters!")
    return url

k_clip_prefix = "[cart]"
k_clip_suffix = "[/cart]"

def read_raw_from_clip(clip):
    if clip.startswith(k_clip_prefix) and clip.endswith(k_clip_suffix):
        return bytes.fromhex(clip[len(k_clip_prefix):-len(k_clip_suffix)])        
    else:
        throw("Invalid clipboard tag")

def read_cart_from_clip(clip, **opts):
    data = read_raw_from_clip(clip)
    return read_cart_from_image(data, **opts)

def write_raw_to_clip(data):
    return k_clip_prefix + data.hex() + k_clip_suffix

def write_cart_to_clip(cart, **opts):
    return write_raw_to_clip(write_cart_to_image(cart, **opts))

def read_cart_autodetect(path, **opts):
    try:
        text = file_read_text(path)

        # cart?
        if text.startswith(k_p8_prefix) or text.startswith("__lua__"):
            return read_cart_from_source(text, path=path, **opts)
            
        rtext = text.rstrip()

        # clip?
        if rtext.startswith(k_clip_prefix):
            return read_cart_from_clip(rtext, path=path, **opts)

        # url?
        if rtext.startswith(k_url_prefix):
            return read_cart_from_url(rtext, path=path, **opts)

        # plain text?
        return read_cart_from_source(text, raw=True, path=path, **opts)
        
    except UnicodeDecodeError: # required to happen for pngs
        return read_cart(path, CartFormat.png, **opts)

def read_cart(path, format=None, **opts):
    """Read a cart from the given path, assuming it is in the given format"""
    if format in (CartFormat.p8, CartFormat.code):
        return read_cart_from_source(file_read_text(path), path=path, **opts)
    elif format == CartFormat.png:
        return read_cart_from_image(file_read(path), path=path, **opts)
    elif format in (CartFormat.rom, CartFormat.tiny_rom):
        return read_cart_from_rom(file_read(path), path=path, allow_tiny=True, **opts)
    elif format == CartFormat.clip:
        return read_cart_from_clip(file_read_text(path).rstrip(), path=path, **opts)
    elif format == CartFormat.url:
        return read_cart_from_url(file_read_text(path).rstrip(), path=path, **opts)
    elif format == CartFormat.lua:
        return read_cart_from_source(file_read_text(path), raw=True, path=path, **opts)
    elif format in (CartFormat.js, CartFormat.pod):
        return read_cart_export(path, format).read_cart(**opts)
    elif format in (None, CartFormat.auto):
        return read_cart_autodetect(path, **opts)
    else:
        throw(f"invalid format for reading: {format}")

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

class PicoPreprocessor:
    """The standard pico8 preprocessor (supporting #include and nothing else)"""

    def __init__(m, strict=True, include_notifier=None):
        m.strict = strict
        m.include_notifier = include_notifier
        
    def start(m, path, code):
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
            return True, end_i, end_i, out_i
        else:
            return True, i + 1, start_i, out_i

    def handle_inline(m, path, code, i, start_i, out_i, outparts, outmappings):
        return True, i + 1, start_i, out_i
        
    def finish(m, path, code):
        pass

k_long_brackets_re = re.compile(r"\[(=*)\[(.*?)\]\1\]", re.S)
k_wspace = " \t\r\n"

def preprocess_code(path, code, start_line=0, preprocessor=None):
    """preprocess the given pico8 code (e.g. handle #include-s)"""
    outparts = []
    outmappings = []
    i = start_i = out_i = 0
    active = True
    
    if preprocessor is None:
        preprocessor = PicoPreprocessor()
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
    """Writes a cart to the given path in the given format"""
    if format == CartFormat.p8:
        file_write_text(path, write_cart_to_source(cart, **opts))
    elif format == CartFormat.png:
        file_write(path, write_cart_to_image(cart, **opts))
    elif format == CartFormat.rom:
        file_write(path, write_cart_to_rom(cart, **opts))
    elif format == CartFormat.tiny_rom:
        file_write(path, write_cart_to_tiny_rom(cart, **opts))
    elif format == CartFormat.clip:
        file_write_text(path, write_cart_to_clip(cart, **opts))
    elif format == CartFormat.url:
        file_write_text(path, write_cart_to_url(cart, **opts))
    elif format == CartFormat.lua:
        file_write_text(path, write_cart_to_raw_source(cart, **opts))
    elif format == CartFormat.code:
        file_write_text(path, write_cart_to_raw_source(cart, with_header=True, **opts))
    elif format in (CartFormat.js, CartFormat.pod):
        write_or_edit_cart_export(path, cart, format, **opts)
    else:
        throw(f"invalid format for writing: {format}")

def get_bbs_cart_url(id):
    if not id.startswith("#"):
        throw("invalid bbs id - # prefix expected")

    from urllib.parse import urlencode
    params = {"lid": id[1:], "cat": 7}

    return "https://www.lexaloffle.com/bbs/get_cart.php?" + urlencode(params)

from pico_export import read_cart_export, write_or_edit_cart_export
