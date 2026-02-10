from utils import *
from media_utils import Surface, Color, PixelFormat
from pico_cart import load_image_of_size, get_res_path, pico_base64_decode, pico_base64_encode
from pico_cart import k_png_header, k_qoi_header
from pico_export import lz4_uncompress, lz4_compress
from pico_defs import decode_luastr, encode_luastr
from pico_compress import print_size, compress_code, uncompress_code, encode_p8str, decode_p8str
from picotron_defs import get_default_picotron_runtime, get_picotron_version_id, Cart64Glob, k_palette_64
from picotron_fs import PicotronFile, PicotronDir, k_pod, k_pod_prefix_strs, UserData

class Cart64Format(Enum):
    """An enum representing the supported cart formats"""
    auto = p64 = png = rom = tiny_rom = lua = pod = dir = dat = html = bin = fs = label = ...
    
    @property
    def is_input(m):
        return m != m.bin
    @property
    def is_output(m):
        return m != m.auto
    @property
    def is_ext(m):
        return m not in (m.auto, m.dir, m.fs, m.label, m.tiny_rom)
    @property
    def is_src(m):
        return m in (m.p64, m.lua, m.pod, m.dir, m.fs)
    @property
    def is_export(m):
        return m in (m.dat, m.html, m.bin)
    @property
    def is_exposed(m):
        return m != m.fs
    
    @classproperty
    def default_src(m):
        return m.p64
    @classproperty
    def default_dir(m):
        return m.dir

k_info_file = ".info.pod"
k_label_png_file = "label.png"
k_label_qoi_file = "label.qoi"
k_label_files = (k_label_qoi_file, k_label_png_file)

class Cart64:
    """A picotron cart - a collection of all its files"""
    def __init__(m, path="", name=""):
        m.version_id = get_picotron_version_id(get_default_picotron_runtime())
        m.path = path
        m.name = name if name else path_basename(path) if path else ""
        m.files = {}
        m.raw_title = m.raw_label = m.raw_icon = m.raw_home = m.raw_runtime_version = None

    @property
    def metadata(m):
        info = m.files.get(k_info_file)
        return info.metadata if info else None

    def set_metadata(m, key, value):
        info = m.files.get(k_info_file)
        if info and e(meta := info.metadata):
            meta[key] = value
            info.metadata = meta
            return True

    @property
    def title(m):
        if e(m.raw_title):
            return m.raw_title

        meta = m.metadata
        if not meta:
            return ()
        title = str(meta.get("title", ""))
        version = str(meta.get("version", ""))
        author = str(meta.get("author", ""))
        return (title, " ".join((version, ("by " + author if author else ""))))

    def set_raw_title(m, title_lines):
        m.raw_title = title_lines

    @property
    def label(m):
        if m.raw_label:
            return m.raw_label
        
        for label_file in k_label_files:
            label = m.files.get(label_file)
            if e(label):
                return label_file, label
        
        return None, None

    def load_label(m):
        label_file, label = m.label
        if label:
            try:
                check(label.is_raw, "label is not a raw file")
                return load_image_of_size(BytesIO(label.raw_payload), k_label_size, is_qoi=label_file == k_label_qoi_file)
            except CheckError as e:
                eprint("ignoring invalid label due to: %s" % e)
    
    def set_raw_label(m, label_file, label):
        m.raw_label = (label_file, label)

    @property
    def icon(m):
        if m.raw_icon:
            return m.raw_icon

        meta = m.metadata
        icon = meta.get("icon") if meta else None
        return icon if isinstance(icon, UserData) else None

    def load_icon(m):
        icon = m.icon
        if icon and icon.type == "u8" and icon.width and icon.height:
            data = bytearray()
            for i in bytes.fromhex(icon.data):
                if i >= len(k_palette_64):
                    i = 0
                data += bytes(k_palette_64[i] if i else Color(0, 0, 0, 0))
            return Surface.from_data(icon.width, icon.height, PixelFormat.rgba8, data)

    def set_raw_icon(m, icon):
        m.raw_icon = icon

    @property
    def export_home(m):
        if e(m.raw_home):
            return m.raw_home
        meta = m.metadata
        home = meta.get("export_home") if meta else None
        return home if isinstance(home, str) else ""

    def set_raw_export_home(m, value):
        m.raw_home = value

    def get_runtime_version(m, default=sys.maxsize):
        if e(m.raw_runtime_version):
            return m.raw_runtime_version
        meta = m.metadata
        runtime = meta.get("runtime") if meta else None
        return runtime if isinstance(runtime, (int, float)) else default

    @lazy_property
    def runtime_version(m):
        return m.get_runtime_version()

    def set_raw_runtime_version(m, runtime):
        m.raw_runtime_version = runtime

    def set_version(m, runtime):
        m.set_raw_runtime_version(runtime)
        m.version_id = get_picotron_version_id(runtime)
        m.set_metadata("runtime", runtime)
    
k_cart64_size = 0x40000 # + 0x2000 ?
k_rom_header_sig = b"p64"
k_rom_header_size = 8

def print_rom_compressed_size(size, **kwargs):
    print_size("compressed", size, k_cart64_size, **kwargs)

def read_cart64_from_rom(buffer, path=None, allow_tiny=False, size_handler=None, debug_handler=None, **opts):
    cart = Cart64(path=path)
    
    with BinaryReader(BytesIO(buffer)) as r:
        if r.bytes(3) == k_rom_header_sig:
            cart.version_id = r.u8()
            size = r.u32()
            if size_handler:
                print_rom_compressed_size(k_rom_header_size + size, prefix="input", handler=size_handler)
            uncbuffer = lz4_uncompress(r.bytes(size), debug=debug_handler)
            
            with BinaryReader(BytesIO(uncbuffer)) as r:
                while not r.eof():
                    fspath = decode_luastr(r.zbytes())
                    if fspath.endswith("/"):
                        cart.files[fspath] = PicotronDir()
                    else:
                        size = r.u8()
                        if size == 0xff:
                            size = r.u32()
                        data = r.bytes(size)

                        cart.files[fspath] = PicotronFile(data)
            return cart
        
        elif allow_tiny:
            r.rewind()
            r.big_end = True
            tiny_cart = Cart64()
            tiny_code = encode_p8str(uncompress_code(r, max_code_size=sys.maxsize, **opts))
            tiny_cart.files[k_p64_main_path] = PicotronFile(tiny_code)
            return tiny_cart

        else:
            throw("wrong rom header")

def ext_order_key(pair):
    # try to order things to maximize compression
    dirname, filename = str_split_last(pair[0], "/")
    if filename == "":
        # put all directories first and in proper order, in case it matters
        return (-10, "", dirname, filename) # (intentionally reversed from below)
    
    ext = path_extension(filename)
    if filename == "main.lua":
        order = 1
    elif ext == ".lua":
        order = 0
    elif ext == ".pod":
        order = 2
    elif ext == ".gfx":
        order = 3
    elif ext == ".sfx":
        order = 4
    elif ext == ".map":
        order = 5
    else:
        order = 6
    return (order, ext, filename, dirname)

def write_cart64_to_rom(cart, size_handler=None, debug_handler=None, padding=0,
                        limit=None, fast_compress=False, **opts):
    io = BytesIO()

    with BinaryWriter(io) as w:
        for fspath, file in sorted(cart.files.items(), key=ext_order_key):
            w.zbytes(encode_luastr(fspath))
            check(not fspath.endswith("/") == e(file.data), "wrong picotron file/directory path")
            if e(file.data):
                data = file.data
                if len(data) < 0xff:
                    w.u8(len(data))
                else:
                    w.u8(0xff)
                    w.u32(len(data))
                w.bytes(data)

        compressed = lz4_compress(io.getvalue(), fast=fast_compress, debug=debug_handler)
    
    size = k_rom_header_size + len(compressed)
    if size_handler:
        print_rom_compressed_size(size, handler=size_handler)
    if limit:
        check(size <= limit, "cart takes too much compressed space!")
    
    io = BytesIO()
    with BinaryWriter(io) as w:
        w.bytes(k_rom_header_sig)
        w.u8(cart.version_id)
        w.u32(len(compressed))
        w.bytes(compressed)

        for _ in range(padding):
            w.u8(0)

        return io.getvalue()

def write_cart64_to_tiny_rom(cart, size_handler=None, debug_handler=None, **opts):
    main = cart.files.get(k_p64_main_path)
    check(main, f"{k_p64_main_path} not found in cart")
    data = main.raw_payload

    tiny_cart = Cart64()
    tiny_cart.files[k_p64_main_path] = PicotronFile(data)
    compressed_lz4 = write_cart64_to_rom(tiny_cart, debug_handler=debug_handler, **opts)

    io = BytesIO()
    with BinaryWriter(io, big_end = True) as w:
        compress_code(w, decode_p8str(data), force_compress=True)
        compressed_pxa = io.getvalue()

    result = data
    if len(compressed_pxa) < len(result):
        result = compressed_pxa
    if len(compressed_lz4) < len(result):
        result = compressed_lz4

    if size_handler:
        print_rom_compressed_size(len(result), handler=size_handler)

    return result
    
k_cart64_image_size = Point(512, 384)
k_label_size = Point(480, 270)
k_label_offset = Point(16, 38)
k_title_offset = Point(80, 330)
k_title_width = 352 # ?
k_subtitle_suboffset = Point(0, 26)

def read_cart64_from_image(data, **opts):
    image = load_image_of_size(BytesIO(data), k_cart64_image_size)
    width, height = image.size

    io = BytesIO()
    pixels = image.pixels

    with BinaryBitWriter(io) as bw:
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                bw.bits(11, (r & 7) | ((g & 7) << 3) | ((b & 7) << 6) | ((a & 3) << 9))

        data = io.getvalue()

    cart = read_cart64_from_rom(data, **opts)

    _, label = cart.label
    if label is None:
        label = Surface.create(*k_label_size)
        label_pixels = label.pixels
        
        for y in range(k_label_size.y):
            for x in range(k_label_size.x):
                r, g, b, a = pixels[k_label_offset.x + x, k_label_offset.y + y]
                label_pixels[x, y] = (r & ~7, g & ~7, b & ~7, 0xff)

        try:
            cart.files[k_label_qoi_file] = PicotronFile(label.save(format="qoi"))
        except KeyError:
            cart.files[k_label_png_file] = PicotronFile(label.save())
    
    return cart

def draw_title_on_image(image, title, subtitle, offset, width, suboffset):
    # TODO: there seems to be some kerning?!

    with file_open(path_join(get_res_path(), "font64.png")) as font_f:
        font_surf = Surface.load(font_f).alpha
        font_pixels = font_surf.pixels
        char_widths = {}

        for sub in (False, True):
            scale = 1 if sub else 2

            if sub:
                color = Color.gray(0x90)
                scaled_surf = font_surf
                color2 = scaled_surf2 = None
            else:
                color = Color.gray(0xd0)
                scaled_surf = font_surf.scale(2)
                color2 = Color.gray(0x80)
                scaled_surf2 = scaled_surf.copy()
                for y in range(scaled_surf.height):
                    (scaled_surf if y % 2 else scaled_surf2).fill(0, Rect(0, y, scaled_surf.width, 1))
            
            x, y = 0, 0
            for ch in title:
                chi = ord(ch)
                ch_x, ch_y = chi % 16 * 10, chi // 16 * 11
                ch_w = char_widths.get(chi)
                if ch_w is None:
                    ch_w = 0
                    while font_pixels[ch_x + ch_w, ch_y + 9]: # using an "underline" to measure char advance
                        ch_w += 1
                    char_widths[chi] = ch_w
                
                chrect = Rect(ch_x * scale, ch_y * scale, ch_w * scale, 9 * scale)
                new_x = x + chrect.w
                if new_x <= width:
                    dest = Rect.from_pos_size(offset + Point (x, y), chrect.size)
                    image.fill(color, dest, scaled_surf.slice(chrect))
                    if scaled_surf2:
                        image.fill(color2, dest, scaled_surf2.slice(chrect))
                x = new_x
            
            offset += suboffset
            title = subtitle

def write_cart64_to_image(cart, template_image=None, template_only=False, optimize_image=False, **opts):
    output = write_cart64_to_rom(cart, limit=k_cart64_size, padding=4, **opts) # some padding to easily tell when we're done without failing
    end_pos = len(output) - 2

    if not template_image:
        template_image = path_join(get_res_path(), "template64.png")

    with file_open(template_image) as template_f:
        image = load_image_of_size(template_f, k_cart64_image_size)
        width, height = image.size

        if not template_only:
            label = cart.load_label()
            if label:
                image.draw(label, k_label_offset)
            
            title = cart.title
            if title:
                draw_title_on_image(image, *list_unpack(title, 2), k_title_offset, k_title_width, k_subtitle_suboffset)
        
        pixels = image.pixels

        with BinaryBitReader(BytesIO(output)) as br:
            for y in range(height):
                for x in range(width):
                    word = br.bits(11) if br.pos() < end_pos else 0
                    r, g, b, a = pixels[x,y]
                    r = (r & ~7) | (word & 7)
                    g = (g & ~7) | ((word >> 3) & 7)
                    b = (b & ~7) | ((word >> 6) & 7)
                    a = (a & ~3) | ((word >> 9) & 3)
                    pixels[x, y] = (r, g, b, a)

        if optimize_image:
            return image.save(optimize=True)
        else:
            return image.save()

def read_cart64_label(data, path=None, **_):
    cart = Cart64(path=path)
    if data.startswith(k_png_header):
        label_file = k_label_png_file
    elif data.startswith(k_qoi_header):
        label_file = k_label_qoi_file
    else:
        throw("label in unexpected format")
    
    cart.files[label_file] = PicotronFile(data)
    return cart

def write_cart64_label(cart, **_):
    label = cart.load_label()
    if label:
        return label.save()
    else:
        throw("no label to write")

k_p64_prefix = b"picotron cartridge"
k_p64_main_path = "main.lua"
k_p64_file_prefix = b":: "
k_p64_b64_prefix = b"b64$"
k_p64_b64_line_size = 76
k_p64_end_file = "[eoc]"

def read_cart64_from_source(data, path=None, raw=False, **_):
    cart = Cart64(path=path)
    
    if not raw and not data.startswith(k_p64_prefix) and not data.startswith(k_p64_file_prefix): # fallback to raw
        raw = True

    fspath = k_p64_main_path if raw else None
    lines = []
    line_start = 0

    def flush():
        if fspath:
            if fspath.endswith("/"):
                cart.files[fspath] = PicotronDir()
            else:
                data = b"\n".join(lines)
                if data.startswith(k_p64_b64_prefix):
                    data = pico_base64_decode(data[4:])

                cart.files[fspath] = PicotronFile(data, line_start)

    for line_i, line in enumerate(data.splitlines()):
        if line.startswith(k_p64_file_prefix) and not raw:
            flush()
            lines = []
            line_start = line_i + 1

            fspath = decode_luastr(line[len(k_p64_file_prefix):].strip())
            if fspath == k_p64_end_file:
                fspath = None

        elif fspath is None and line.startswith(b"version "):
            cart.version_id = int(line.split()[1])

        else:
            lines.append(line)

    if raw:
        flush()
    elif fspath:
        throw(f"expected {k_p64_end_file} in p64")

    return cart

k_max_bad_p64_char_re = re.compile(b"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\xff]|^" + k_p64_file_prefix, re.M)
k_min_bad_p64_char_re = re.compile(b"\x00|^" + k_p64_file_prefix, re.M)

def preview_order_key(pair):
    # we prefer to sort p64 files for better visibility of code, e.g. in the webapp's preview
    # (this is NOT what picotron does currently, hopefully doesn't matter)
    dirname, filename = str_split_last(pair[0], "/")
    if filename == "": # directory itself must be first
        order = -3
    elif filename == k_p64_main_path:
        order = -2
    elif filename.endswith(".lua"):
        order = -1
    elif filename in k_label_files:
        order = 1
    elif filename.startswith("."):
        order = 2
    else:
        order = 0
    return (dirname, order, filename)

def write_cart64_to_source(cart, avoid_base64=False, **opts):
    lines = [k_p64_prefix + b" // www.picotron.net"]
    lines.append(b"version %d" % cart.version_id)
    lines.append(b'')

    bad_p64_char_re = k_min_bad_p64_char_re if avoid_base64 else k_max_bad_p64_char_re

    for fspath, file in sorted(cart.files.items(), key=preview_order_key):
        lines.append(k_p64_file_prefix + encode_luastr(fspath))
        if e(file.data):
            if bad_p64_char_re.search(file.data):
                data = k_p64_b64_prefix + pico_base64_encode(file.data)
                for line in str_chunk(data, k_p64_b64_line_size):
                    lines.append(line)
            else:
                lines.append(file.data)

    lines.append(k_p64_file_prefix + encode_luastr(k_p64_end_file))

    return b"\n".join(lines) + b"\n"

def write_cart64_to_raw_source(cart, **_):
    main = cart.files.get(k_p64_main_path)
    check(main, "{k_p64_main_path} not found in cart")
    return main.data

k_fictive_main_pod = "main.pod" # not a real picotron concept

def read_cart64_from_single_pod(data, path=None, **_):
    cart = Cart64(path=path)
    main = PicotronFile(data)
    if main.raw_metadata is None:
        main.raw_metadata = k_pod
    cart.files[k_fictive_main_pod] = main
    return cart

def write_cart64_to_single_pod(cart, **_):
    main = cart.files.get(k_fictive_main_pod)
    check(main, "{k_fictive_main_pod} not found in cart")
    if main.raw_metadata == k_pod:
        main.raw_metadata = None
    return main.data

def read_cart64_from_fs(path, is_dir=None, target_cart=None, fspath=None, sections=None, **opts):
    if target_cart is None:
        target_cart = Cart64(path=path)
    if fspath is None or fspath in (".", "/"):
        fspath = ""
    if sections and not isinstance(sections, Cart64Glob):
        sections = Cart64Glob(sections)
    
    if is_dir is None:
        is_dir = path_is_dir(path)

    if is_dir:
        if fspath:
            if not fspath.endswith("/"):
                fspath += "/"
            target_cart.files[fspath] = PicotronDir()

        for child in dir_names(path):
            child_path = path_join(path, child)
            child_fspath = fspath + child
            read_cart64_from_fs(child_path, None, target_cart, child_fspath, sections, **opts)
    else:
        if not fspath or fspath.endswith("/"):
            fspath += path_basename(path) # good default
        if not sections or sections.matches(fspath):
            check(not fspath.endswith("/"), "filenames cannot end with '/'")
            target_cart.files[fspath] = PicotronFile(file_read(path))

    return target_cart

def write_cart64_to_fs(cart, path, is_dir=None, fspath=None, delete_existing=False, **opts):
    if fspath is None:
        fspath = ""
    
    if is_dir is None:
        file = cart.files.get(fspath)
        is_dir = file.is_dir if file else False

    if is_dir:
        if fspath and not fspath.endswith("/"):
            fspath += "/"
        dir_create(path, delete_existing=delete_existing)

        for child_fspath, file in cart.files.items():
            if child_fspath.startswith(fspath):
                child = child_fspath[len(fspath):]
                if child.count("/") == (1 if file.is_dir else 0):
                    child_path = path_join(path, child)
                    check(path_is_inside(child_path, path), f"'{child_path}' is outside '{path}'")
                    write_cart64_to_fs(cart, child_path, file.is_dir, child_fspath, **opts)
    else:
        if path_is_dir(path):
            path = path_join(path, path_basename(fspath)) # good default
        file = cart.files.get(fspath)
        check(file, f"no file '{fspath}' in cart")
        file_write(path, file.data)

def read_cart64_autodetect(path, **opts):
    if path_is_native(path) and path_is_dir(path):
        return read_cart64_from_fs(path, is_dir=True, **opts)

    data = file_read(path)

    # cart?
    if data.startswith(k_p64_prefix):
        return read_cart64_from_source(data, path=path, **opts)
    
    # png?
    if data.startswith(k_png_header):
        return read_cart64_from_image(data, path=path, **opts)

    # rom?
    if data.startswith(k_rom_header_sig) and b"\0" in data[:k_rom_header_size]: # the rom size must have a nul
        return read_cart64_from_rom(data, path=path, **opts)
        
    # plain text?
    return read_cart64_from_source(data, raw=True, path=path, **opts)

def read_cart64(path, format=None, **opts):
    """Read a cart from the given path, assuming it is in the given format"""
    if format in (None, Cart64Format.auto):
        return read_cart64_autodetect(path, **opts)
    elif format == Cart64Format.p64:
        return read_cart64_from_source(file_read(path), path=path, **opts)
    elif format == Cart64Format.png:
        return read_cart64_from_image(file_read(path), path=path, **opts)
    elif format in (Cart64Format.rom, Cart64Format.tiny_rom):
        return read_cart64_from_rom(file_read(path), path=path, allow_tiny=True, **opts)
    elif format == Cart64Format.lua:
        return read_cart64_from_source(file_read(path), raw=True, path=path, **opts)
    elif format == Cart64Format.pod:
        return read_cart64_from_single_pod(file_read(path), path=path, **opts)
    elif format in (Cart64Format.dir, Cart64Format.fs):
        return read_cart64_from_fs(path, is_dir=True if format == Cart64Format.dir else None, **opts)
    elif format == Cart64Format.label:
        return read_cart64_label(file_read(path), path=path, **opts)
    elif format.is_export:
        return read_cart64_export(path, format).get_cart(path=path, **opts)
    else:
        throw(f"invalid format for reading: {format}")

def write_cart64(path, cart, format, **opts):
    """Writes a cart to the given path in the given format"""
    if format == Cart64Format.p64:
        file_write(path, write_cart64_to_source(cart, **opts))
    elif format == Cart64Format.png:
        file_write(path, write_cart64_to_image(cart, **opts))
    elif format == Cart64Format.rom:
        file_write(path, write_cart64_to_rom(cart, **opts))
    elif format == Cart64Format.tiny_rom:
        file_write(path, write_cart64_to_tiny_rom(cart, **opts))
    elif format == Cart64Format.lua:
        file_write(path, write_cart64_to_raw_source(cart, **opts))
    elif format == Cart64Format.pod:
        file_write(path, write_cart64_to_single_pod(cart, **opts))
    elif format in (Cart64Format.dir, Cart64Format.fs):
        write_cart64_to_fs(cart, path, is_dir=True if format == Cart64Format.dir else None, **opts)
    elif format == Cart64Format.label:
        file_write(path, write_cart64_label(cart, **opts))
    elif format.is_export:
        write_to_cart64_export(path, cart, format, **opts)
    else:
        throw(f"invalid format for writing: {format}")

def filter_cart64(cart, sections):
    glob = Cart64Glob(sections)
    to_delete = [path for path in cart.files if not glob.matches(path)]
    for path in to_delete:
        del cart.files[path]

def preproc_meta(cart, delete_meta, keep_meta_keys):
    to_delete = []
    glob = Cart64Glob(delete_meta)
    key_glob = Cart64Glob(keep_meta_keys)

    for path, file in cart.files.items():
        if glob.matches(path) and not file.is_dir:
            meta = file.metadata
            new_meta = None
            if e(meta):
                new_meta = {}
                for key, value in meta.items():
                    if key_glob.matches(key):
                        new_meta[key] = value
                
                if new_meta:
                    for req_key in k_pod_prefix_strs: # at least the format
                        if req_key in meta:
                            new_meta[req_key] = meta[req_key]
                else:
                    if file.is_raw:
                        new_meta = None
            
            if not new_meta and str_after_last(path, "/") == ".info.pod": # contains meta only
                to_delete.append(path)
            else:
                file.metadata = new_meta
    
    for path in to_delete:
        del cart.files[path]

def preproc_cart64(cart, delete_meta=None, keep_meta_keys=None, delete_label=None,
                   uncompress_pods=False, base64_pods=False, keep_pod_compression=False, need_pod_compression=False):
    if delete_meta:
        cart.set_raw_title(cart.title)
        cart.set_raw_icon(cart.icon)
        cart.set_raw_export_home(cart.export_home)
        cart.set_raw_runtime_version(cart.get_runtime_version())
        preproc_meta(cart, delete_meta, keep_meta_keys)
    
    if delete_label:
        label_file, label = cart.label
        for any_label_file in k_label_files:
            cart.files.pop(any_label_file, None)
        cart.set_raw_label(label_file, label)
    
    if not keep_pod_compression:
        runtime = cart.runtime_version
        for path, file in cart.files.items():
            if not file.is_raw and not file.is_dir:
                if uncompress_pods:
                    file.set_payload(file.payload, compress=False, use_pxu=False, use_base64=base64_pods, runtime=runtime)
                elif need_pod_compression:
                    file.set_payload(file.payload, compress=True, use_pxu=True, use_base64=base64_pods, runtime=runtime)
                else:
                    file.set_payload(file.payload, compress=False, use_pxu=True, use_base64=base64_pods, runtime=runtime)

def merge_cart64(dest, src, sections=None):
    glob = Cart64Glob(sections) if e(sections) else None
    for path, file in sorted(src.files.items()): # sort to get dirs first
        if not glob or glob.matches(path):
            dest.files[path] = file
            
            # create parent directories
            parent = str_before_last(path.rstrip("/"), "/") + "/"
            while parent != "/" and parent not in dest.files:
                dest.files[parent] = PicotronDir()
                parent = str_before_last(parent[:-1], "/") + "/"

def write_cart64_compressed_size(cart, handler=True, **opts):
    write_cart64_to_rom(cart, size_handler=handler, **opts)

def write_cart64_version(cart):
    print("version: %d" % cart.version_id)
    print("runtime version: %d" % cart.get_runtime_version(-1))

from picotron_export import read_cart64_export, write_to_cart64_export
