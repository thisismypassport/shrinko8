from utils import *
from sdl2_utils import Surface, Color, Palette, PixelFormat
from pico_defs import *
from pico_cart import CartFormat, write_cart, read_cart_from_rom, write_cart_to_rom
from pico_cart import read_cart_from_source, write_cart_to_source, create_screenshot_surface
from pico_compress import get_lz77, Lz77Entry

class ListOp(Enum):
    insert = replace = delete = rename = ...

class CartExport:
    """A container of multiple carts"""

    # get_carts_impl: () -> {name: <ref>} in cart order
    # read_impl: (<ref>, **opts) -> cart
    # insert_impl: (<ref> or None, name, cart, **opts) -> void
    # replace_impl: (<ref>, cart, **opts) -> void
    # delete_impl: (<ref>, **opts) -> void
    # rename_impl: (<ref>, new_name, **opts) -> void
    # NOTE: <ref>s are valid only until next modification or get_carts_impl call

    def _default(m, carts, strict=True):
        name = dict_first_key(carts)
        if name is None and strict:
            throw(f"export is empty - contains no carts")
        return name

    def _find(m, carts, cart_name, strict=True):
        ref = carts.get(cart_name)
        if ref is None and strict:
            throw(f"cart {cart_name} not found in export")
        return ref

    def _contains(m, carts, cart_name):
        return e(m._find(carts, cart_name, strict=False))
    
    def list_carts(m):
        return m.get_carts_impl().keys()

    def read_cart(m, cart_name=None, **opts):
        carts = m.get_carts_impl()
        if cart_name is None:
            cart_name = m._default(carts)
        ref = m._find(carts, cart_name)

        return m.read_impl(ref, path=cart_name, **opts)
    
    def write_cart(m, cart, cart_name=None, cart_op=None, target_name=None, **opts):
        cart_op = default(cart_op, ListOp.insert)
        carts = m.get_carts_impl()

        if cart_op == ListOp.insert:
            if cart_name is None:
                cart_name = cart.name
            if m._contains(carts, cart_name):
                throw(f"cart {cart_name} already found in export")
            
            target_ref = None
            if e(target_name):
                target_ref = m._find(carts, target_name)
            m.insert_impl(target_ref, cart_name, cart, **opts)

        else:
            if cart_name is None:
                cart_name = m._default(carts)
            ref = m._find(carts, cart_name)
            
            if cart_op == ListOp.replace:
                m.replace_impl(ref, cart, **opts)
            elif cart_op == ListOp.delete:
                m.delete_impl(ref)
            elif cart_op == ListOp.rename:
                if m._contains(carts, target_name):
                    throw(f"cart {target_name} already found in export")
                
                m.rename_impl(ref, target_name)
            else:
                fail("invalid cart op")
        
        return m

    def dump_cart(m, dest, fmt, name, raw_data):
        path = path_join(dest, filename_fixup(name))

        if fmt == CartFormat.rom:
            file_write(path, raw_data)
        else:
            write_cart(path, read_cart_from_rom(raw_data), fmt)

class JsExport(CartExport):
    """A javascript file containing one or more carts"""

    def __init__(m, text):
        super().__init__()
        m.text = text
    
    def find_cartnames(m):
        match = re.search("var\s+_cartname\s*=\s*\[(.*?)\]", m.text, re.S)
        if not match:
            throw("can't find _cartname var in js")
        return match
    
    def find_cartdata(m):
        match = re.search("var\s+_cartdat\s*=\s*\[(.*?)\]", m.text, re.S)
        if not match:
            throw("can't find _cartdat var in js")
        return match

    def get_carts_impl(m):
        m.cartnames = []
        cartnames_text = m.find_cartnames().group(1)
        if cartnames_text.strip():
            for i, cartname in enumerate(cartnames_text.split(",")):
                cartname = cartname.strip()[1:-1] # may fail if using special chars...
                m.cartnames.append(cartname)

        m.cartdata = bytearray(k_cart_size * len(m.cartnames))
        cartdata_text = m.find_cartdata().group(1)
        if cartdata_text.strip():
            for i, b in enumerate(cartdata_text.split(",")):
                m.cartdata[i] = int(b.strip())

        carts = {}
        for i, cartname in enumerate(m.cartnames):
            carts[cartname] = i
        return carts

    def slice(m, i, end_i=None):
        return slice(k_cart_size * i, k_cart_size * default(end_i, i + 1))

    def read_impl(m, i, **opts):
        return read_cart_from_rom(m.cartdata[m.slice(i)], **opts)

    def insert_impl(m, i, name, cart, **opts):
        i = default(i, len(m.cartnames))
        m.cartdata[m.slice(i, i)] = write_cart_to_rom(cart, **opts)
        m.cartnames.insert(i, name)
        m.finish_write()

    def replace_impl(m, i, cart, **opts):
        m.cartdata[m.slice(i)] = write_cart_to_rom(cart, **opts)
        m.finish_write()
    
    def delete_impl(m, i):
        del m.cartdata[m.slice(i)]
        del m.cartnames[i]
        m.finish_write()
    
    def rename_impl(m, i, name):
        m.cartnames[i] = name
        m.finish_write()

    def finish_write(m):
        cartnames_text = ", ".join(f"`{name}`" for name in m.cartnames)
        m.text = str_replace_between(m.text, *m.find_cartnames().span(1), cartnames_text)

        cartdata_chunks = ["\n"]
        for chunk in iter_chunk(m.cartdata, 0x100):
            if len(cartdata_chunks) > 1:
                cartdata_chunks.append(",\n")
            cartdata_chunks.append(",".join("%d" % b for b in chunk))
        m.text = str_replace_between(m.text, *m.find_cartdata().span(1), "".join(cartdata_chunks))
        m.cartnames = m.cartdata = None # need reparse
    
    def find_pod(m):
        matches = list(re.finditer("fileData0\.push\.apply\s*\(\s*fileData0\s*,\s*\[(.*?)\]\s*\)", m.text, re.S))
        if not matches:
            throw("can't find fileData0 pushes in js")
        return matches
    
    def read_pod(m): # this pod is the same for all carts, so it's not very interesting in retrospect
        pod_data = bytearray()
        for match in m.find_pod():
            match_text = match.group(1)
            if match_text.strip():
                for b in match_text.split(","):
                    pod_data.append(int(b.strip()))
        return PodFile(pod_data)

    def dump_contents(m, dest, fmt, misc=False):
        carts = m.get_carts_impl()
        for name, i in carts.items():
            m.dump_cart(dest, fmt, name, m.cartdata[m.slice(i)])
        if misc:
            m.read_pod().dump_contents(dest, fmt, misc=True)
    
    @classmethod
    def create(cls, pico8_dat, html_pod=None, for_wasm=False, **_):
        if not html_pod:
            html_pod = PodFile(pico8_dat.find_named("pod/f_html5.pod"))
        js_file = "var _cartname=[];\n"
        js_file += "var _cdpos=0; var iii=0; var ciii=0;\n"
        js_file += "var _cartdat=[];\n\n"
        js_file += html_pod.find_named("src/pico8_wasm.js" if for_wasm else "src/pico8.js").decode()
        return JsExport(js_file)        

class PodFile:
    """A pod file - used in pico8 inside exports/etc"""

    k_header = "CPOD"
    k_file_header = "CFIL"
    k_cmpr_file_header = "cFIL"
    k_bmp_header = "CBMP"
    k_cmpr_bmp_header = "cBMP"
    k_pal_header = "CPAL"
    k_num_colors = 0x100

    class Entry(Struct):
        header = pos = end_pos = name = content = ...

    def __init__(m, data):
        m.data = data
        m.read_all()

    def init_write(m):
        if not isinstance(m.data, bytearray):
            m.data = bytearray(m.data)

    def read_all(m):
        with BinaryReader(BytesIO(m.data)) as r:
            check(r.str(4) == m.k_header, "invalid POD file")
            check(r.u32() == 0x44, "newer POD version?") # size of header?
            check(r.u32() == 1, "newer POD version?") # ???
            m.name = r.zstr(0x20) # ???
            count = r.u32()
            r.addpos(0x1c) # junk?

            m.entries = []
            palette = None
            for i in range(count):
                pos = r.pos()
                header = r.str(4)
                name = None

                if header in (m.k_file_header, m.k_cmpr_file_header):
                    check(r.u32() == 0, "unknown POD file header value")
                    size = r.u32()
                    name = r.zstr(0x40)
                    if header == m.k_cmpr_file_header:
                        content = m.lz4_uncompress(r.bytes(r.u32()))
                    else:
                        content = r.bytes(size)
                
                elif header in (m.k_bmp_header, m.k_cmpr_bmp_header):
                    size = r.u32()
                    w = r.u32()
                    h = r.u32()
                    bpp = r.u32()
                    check(r.u32() == 0, "unknown POD bmp header value")
                    check(r.u32() == 0, "unknown POD bmp header value")
                    if header == m.k_cmpr_bmp_header:
                        data = m.lz4_uncompress(r.bytes(r.u32()))
                    else:
                        data = r.bytes(size - 0x14)
                    
                    fmt = PixelFormat.i8 if bpp == 8 else PixelFormat.bgra8 if bpp == 32 else throw("unknown POD bmp bpp %d" % bpp)
                    content = Surface.from_data(w, h, fmt, data)
                    if fmt == PixelFormat.i8:
                        content.palette = default(palette, m.default_palette)

                elif header == m.k_pal_header:
                    size = r.u32()
                    num_colors = m.k_num_colors
                    check(size == 3 * num_colors, "wrong POD palette size?")
                    content = Palette.create(num_colors)
                    for i in range(num_colors):
                        content[i] = Color(r.u8(), r.u8(), r.u8())

                else:
                    throw("unknown or unexpected POD content header %s" % header)
                
                end_pos = r.pos()
                m.entries.append(m.Entry(header, pos, end_pos, name, content))
    
    @lazy_classproperty
    def default_palette(cls): # used for fonts in pod - well, the 0 and 0xff colors are.
        palette = Palette.create(cls.k_num_colors)
        for i in range(0x100):
            palette[i] = Color(i, i, i)
        return palette
    
    def find_named(m, name, strict=True):
        for e in m.entries:
            if e.name == name:
                return e.content
        if strict:
            throw(f"expected to find {name} in pod")

    def find_prefix(m, prefix, strict=True):
        found = False
        for e in m.entries:
            if e.name.startswith(prefix):
                yield e.name[len(prefix):], e.content
                found = True
        if strict and not found:
            throw(f"expected to find {prefix}* in pod")

    def contains(m, name):
        return m.find_named(name, strict=False) != None

    def shift_entry_positions(m, i, delta):
        for e in m.entries[i:]:
            e.pos += delta
            e.end_pos += delta

    def update_count(m):
        buf = BinaryBuffer(m.data)
        buf.w_u32(0x2c, len(m.entries))
    
    @classmethod
    def create(cls, name=None):
        with BinaryWriter() as w:
            w.str(cls.k_header)
            w.u32(0x44) # size of header
            w.u32(1) # version?
            w.zstr(name or "", 0x20)
            w.u32(0)
            w.zstr("", 0x1c)
        
            return PodFile(w.f.getvalue())

    def insert_content(m, i, name, content, compress=False):
        m.init_write()
        if i < len(m.entries):
            pos = m.entries[i].pos
        else:
            pos = len(m.data)
        
        def write_bytes(w, data):
            if compress:
                compressed = m.lz4_compress(data)
                w.u32(len(compressed))
                w.bytes(compressed)
            else:
                w.bytes(data)
        
        with BinaryWriter() as w:
            if isinstance(content, bytes):
                header = m.k_cmpr_file_header if compress else m.k_file_header

                w.str(header)
                w.u32(0)
                w.u32(len(content))
                w.zstr(name, 0x40)
                write_bytes(w, content)
            
            elif isinstance(content, Surface):
                if content.format.bpp == 8:
                    format = PixelFormat.i8
                elif content.format.bpp == 32:
                    format = PixelFormat.bgra8
                else:
                    check("invalid surface format for pod")
                
                data = content.to_data(format)
                header = m.k_cmpr_bmp_header if compress else m.k_bmp_header

                w.str(header)
                w.u32(len(data) + 0x14)
                w.u32(content.width)
                w.u32(content.height)
                w.u32(content.format.bpp)
                w.u32(0); w.u32(0)
                write_bytes(w, data)

            elif isinstance(content, Palette):
                assert not compress
                header = m.k_pal_header

                w.str(header)
                w.u32(3 * m.k_num_colors)
                for i in range(m.k_num_colors):
                    r, g, b, _ = content[i]
                    w.u8(r); w.u8(g); w.u8(b)
            
            else:
                fail("Unknown content type")
            
            size = w.pos()
            new_data = w.f.getvalue()
        
        m.data[pos:pos] = new_data
        m.entries.insert(i, m.Entry(header, pos, pos + size, name, content))

        m.shift_entry_positions(i + 1, size)
        m.update_count()
        
    def append_content(m, name, content, compress=False):
        m.insert_content(len(m.entries), name, content, compress)

    def delete_content(m, i):
        m.init_write()
        e = m.entries[i]

        del m.data[e.pos:e.end_pos]
        del m.entries[i]

        m.shift_entry_positions(i, -(e.end_pos - e.pos))
        m.update_count()
    
    def replace_content(m, i, content):
        e = m.entries[i]
        if e.header == m.k_file_header and isinstance(content, bytes) and len(content) == len(e.content):
            pos = e.pos + 0x4c
        else:
            m.delete_content(i)
            m.insert_content(i, e.name, content)
            return

        m.init_write()
        m.data[pos:pos+len(content)] = content
        e.content = content
    
    def rename_content(m, i, name):
        m.init_write()
        e = m.entries[i]
        if isinstance(e.content, bytes):
            buf = BinaryBuffer(m.data)
            buf.w_zstr(e.pos + 0xc, name, 0x40)
            e.name = name

    def dump_contents(m, dest, fmt, misc=False):
        for i, e in enumerate(m.entries):
            if isinstance(e.content, bytes):
                m.dump_file(dest, fmt, misc, i, e.name, e.content)
            elif isinstance(e.content, Surface):
                with file_create(path_join(dest, f"{i}.png")) as f:
                    e.content.save(f)
            elif isinstance(e.content, Palette):
                pass # used for the images already
            else:
                fail("wrong data in pod contents")
    
    def dump_file(m, dest, fmt, misc, i, name, content):
        if name.lower().endswith(".pod"):
            pod_dest = path_join(dest, filename_fixup(name[:-4]))
            dir_ensure_exists(pod_dest)
            PodFile(content).dump_contents(pod_dest, fmt, misc)
        else:
            file_write(path_join(dest, filename_fixup(name)), content)

    def lz4_uncompress(m, data):
        def read_u8_sum(r):
            sum = 0
            while True:
                val = r.u8()
                sum += val
                if val != 0xff:
                    return sum

        uncdata = bytearray()
        with BinaryReader(BytesIO(data)) as r:
            while not r.eof():
                header = r.u8()
                size = header >> 4
                if size == 0xf:
                    size += read_u8_sum(r)
                
                for i in range(size):
                    uncdata.append(r.u8())
                
                if not r.eof():
                    offset = r.u16()
                    count = 4 + (header & 0xf)
                    if count == 0x13:
                        count += read_u8_sum(r)
                    
                    for i in range(count):
                        uncdata.append(uncdata[-offset])
        
        return bytes(uncdata)

    def lz4_compress(m, uncdata):
        literals = []
        min_c = 4

        with BinaryWriter() as w:
            def write_u8_sum(val):
                while True:
                    byte = min(val, 0xff)
                    w.u8(byte)
                    val -= byte
                    if byte != 0xff:
                        break

            def write_block(item):
                size = len(literals)
                count = (item.count - min_c) if item else 0

                w.u8(min(count, 0xf) | (min(size, 0xf) << 4))
                if size >= 0xf:
                    write_u8_sum(size - 0xf)
                
                for lit in literals:
                    w.u8(lit)
                literals.clear()

                if item:
                    w.u16(item.offset)
                    if count >= 0xf:
                        write_u8_sum(count - 0xf)

            end_of_lz77_reach = len(uncdata) - 5
            end_of_lz77s = len(uncdata) - 12

            for i, item in get_lz77(uncdata, min_c=min_c, max_c=None, max_o=0xffff):
                if isinstance(item, Lz77Entry):
                    if i < end_of_lz77s:
                        if i + item.count <= end_of_lz77_reach:
                            write_block(item)
                        else:
                            fixed_item = Lz77Entry(item.offset, end_of_lz77_reach - i)
                            assert fixed_item.count >= min_c
                            write_block(fixed_item)
                            literals.extend(uncdata[end_of_lz77_reach:i+item.count])
                    else:                    
                        literals.extend(uncdata[i:i+item.count])
                else:
                    literals.append(item)
            write_block(None)

            return w.f.getvalue()

class PodExport(CartExport, PodFile):
    """A .pod file used in exports, containing one or more carts"""

    k_pod_names = ["pod/pico8_boot.p8", "pod/gfx1.pod", "pod/f_pico8.pod"]

    def __init__(m, data):
        CartExport.__init__(m)
        PodFile.__init__(m, data)

    def get_carts_impl(m):
        carts = {}
        for i, e in enumerate(m.entries):
            if e.name and isinstance(e.content, bytes): # only carts are named in export pod files
                carts[e.name] = (i, e.content)
        return carts

    def read_impl(m, tuple, **opts):
        _, bytes = tuple
        return read_cart_from_rom(bytes, **opts)
    
    def insert_impl(m, tuple, name, cart, **opts):
        if e(tuple):
            i, _ = tuple
        else:
            i = len(m.entries)
        
        new_bytes = write_cart_to_rom(cart, **opts)
        m.insert_content(i, name, new_bytes)

    def replace_impl(m, tuple, cart, **opts):
        i, bytes = tuple
        new_bytes = write_cart_to_rom(cart, **opts)

        if len(new_bytes) != len(bytes):
            throw(f"existing cart has size {len(bytes):#x} vs expected {len(new_bytes):#x}")
        m.replace_content(i, new_bytes)

    def delete_impl(m, tuple):
        i, _ = tuple
        m.delete_content(i)

    def rename_impl(m, tuple, name):
        i, _ = tuple
        m.rename_content(i, name)
        
    def dump_file(m, dest, fmt, misc, i, name, cdata):
        #return super().dump_file(dest, fmt, misc, i, name, cdata) # (uncomment out to dump pico8.dat with '-F pod')
        if name:
            m.dump_cart(dest, fmt, name, cdata)
        elif misc:
            name = m.k_pod_names[i] # names these files have in non-cart pods
            super().dump_file(dest, fmt, misc, i, name, cdata)
            
    @classmethod
    def create(cls, pico8_dat, cart=None, export_name="", **_):
        m = PodExport(PodFile.create().data)

        boot_cart = read_cart_from_source(pico8_dat.find_named(m.k_pod_names[0]).decode())
        if cart:
            boot_cart.version_id = cart.version_id
        m.append_content("", write_cart_to_source(boot_cart).encode())

        for pod_i, pod_name in enumerate(m.k_pod_names):
            if pod_i == 0: # handled above, not a pod
                continue

            pod = PodFile(pico8_dat.find_named(pod_name))
            new_pod = PodFile.create(pod.name)

            for i, e in enumerate(pod.entries):
                content = e.content

                if pod_i == 1 and i == 4:
                    # this is the window title - it's reinterpreted to a bitmap
                    assert content.format.bpp == 8
                    x, y = 0, 0
                    pixels = content.pixels
                    for ch in export_name + "\0":
                        pixels[x, y] = ord(ch)
                        x += 1
                        if x == content.width:
                            x = 0
                            y += 1

                elif pod_i == 1 and i == 6:
                    if cart and cart.label:
                        content = create_screenshot_surface(cart.label)

                new_pod.append_content(e.name, content, compress=isinstance(content, Surface))

            m.append_content("", bytes(new_pod.data))
        return m

class FullExport(CartExport):
    def __init__(m, pico8_dat, cart):
        m.pico8_dat = pico8_dat
        m.cart = cart

    @classmethod
    def create(cls, pico8_dat, cart=None, export_name="", **opts):
        opts["cart"] = cart
        opts["export_name"] = export_name

        m = FullExport(pico8_dat, cart)
        m.html_pod = PodFile(pico8_dat.find_named("pod/f_html5.pod"))
        m.bin_pod = PodFile(pico8_dat.find_named("pod/f_bin.pod"))

        m.pod = PodExport.create(pico8_dat, **opts)
        m.js = JsExport.create(pico8_dat, html_pod=m.html_pod, **opts)
        m.wjs = JsExport.create(pico8_dat, html_pod=m.html_pod, for_wasm=True, **opts)
        m.exports = [m.pod, m.js, m.wjs]
        
        m.export_name = export_name
        m.curr_time = time.localtime(maybe_float(os.getenv("PICO8_EXPORT_REPRO_TIME", time.time())))[:6]
        return m

    def write_cart(m, *args, **opts):
        for export in m.exports:
            export.write_cart(*args, **opts)

    def find_zstr(m, data, prefix, infix):
        start = 0
        while True:
            start = data.find(prefix, start)
            if start < 0:
                break

            end = data.find(b"\0", start)
            if end < 0:
                break
            
            zstr = data[start:end]
            if infix in zstr:
                return zstr.decode()
            
            start = end + 1
        
        raise Exception("'%s' with '%s' not found in data")

    def find_icon_offset_in_exe(m, exe_data):
        r = BinaryReader(BytesIO(exe_data))
        assert r.str(2) == "MZ"
        r.setpos(0x3c)
        r.setpos(r.u32())

        assert r.str(4) == "PE\0\0"
        _, num_sections, _, _, _, opt_header_size, _ = r.u16(), r.u16(), r.u32(), r.u32(), r.u32(), r.u16(), r.u16()
        header_end = r.pos() + opt_header_size

        opt_header = r.u16()
        assert opt_header in (0x10b, 0x20b)
        is64 = (opt_header == 0x20b)
        r.addpos(126 if is64 else 110)
        rsrc_rva = r.u32()

        r.setpos(header_end)
        sections = []
        for _ in range(num_sections):
            r.addpos(0x8)
            vsize, vaddr, _, offset = r.u32(), r.u32(), r.u32(), r.u32()
            r.addpos(0x10)
            sections.append((vaddr, vsize, offset))
        
        def rva_to_offset(rva):
            for vaddr, vsize, offset in sections:
                if rva >= vaddr and rva < vaddr + vsize:
                    return offset + (rva - vaddr)

        rsrc_offset = rva_to_offset(rsrc_rva)
        if rsrc_offset is None:
            eprint("no rsrc in exe")
            return None
        
        def find_rsrc_entry(offset, target):
            if offset & 0x80000000:
                r.setpos(rsrc_offset + (offset & 0x7fffffff) + 0xc)
                num_named, num_indexed = r.u16(), r.u16()
                r.addpos(num_named * 0x8)

                for _ in range(num_indexed):
                    idx, offset = r.u32(), r.u32()
                    if idx == target:
                        return offset
        
        icon_entry = find_rsrc_entry(0x80000000, 3)
        if e(icon_entry):
            icon_entry = find_rsrc_entry(icon_entry, 1)
        if e(icon_entry):
            icon_entry = find_rsrc_entry(icon_entry, 0x409)
        if icon_entry is None or icon_entry & 0x80000000:
            eprint("no english icon #1 in exe")
            return None

        r.setpos(rsrc_offset + icon_entry)
        icon_rva, icon_size = r.u32(), r.u32()
        if icon_size != 0x10828:
            eprint("unknown icon size in exe")
            return None

        icon_offset = rva_to_offset(icon_rva)
        assert e(icon_offset)
        return icon_offset + 0x28

    def create_icns_data(m, raw_data):
        w = BinaryWriter(big_end=True)
        w.str("icns")
        w.u32(0) # filled below
        w.str("it32")
        w.u32(0xc + 0x80 * 0x81 * 3)
        w.u32(0)

        # pico8 doesn't compress, so neither shall we
        for chan in range(3):
            for y in range(0x80):
                w.u8(0x7f)
                for x in range(0x80):
                    w.u8(raw_data[(x + y*0x80)*3 + chan])

        w.str("t8mk")
        mask_len = 0x80 * 0x80
        w.u32(0x8 + mask_len)
        for i in range(mask_len):
            w.u8(0xff)

        w.setpos(4)
        w.u32(w.len())
        return w.f.getvalue()

    def save(m, path):
        import base64
        from zipfile import ZipFile, ZipInfo, ZIP_STORED, ZIP_DEFLATED

        def zip_write(zip, dir, name, data, exec=False, is_dir=False):
            info = ZipInfo(dir + "/" + name, m.curr_time)
            info.create_system = 3 # unix
            info.external_attr = (0o775 if exec or is_dir else 0o644) << 16
            if is_dir:
                info.external_attr |= 0x10 # w/o 0x40000000
                info.compress_type = ZIP_STORED
                info.filename += "/"
                zip.writestr(info, b"") # zip.mkdir is too new...
            else:
                info.external_attr |= 0x80000000
                info.compress_type = ZIP_DEFLATED
                zip.writestr(info, data)
        
        def zip_mkdir(zip, dir, name):
            zip_write(zip, dir, name, None, is_dir=True)
            return dir + "/" + name

        def zip_copy(zip, dir, pod, exclude=None):
            for e in pod.entries:
                if e.name and e.name.startswith("./"): # many unnamed entries?
                    if exclude and exclude in e.name:
                        continue

                    exec = "." not in path_basename(e.name) # ???
                    is_dir = not e.content # ???
                    zip_write(zip, dir, e.name[2:], e.content, exec=exec, is_dir=is_dir)

        dir_ensure_exists(path)
        basename = m.export_name

        label_bmpdata = None
        label_icnsdata = None
        label_png = None
        label_url = ""
        if m.cart and m.cart.label:
            label = create_screenshot_surface(m.cart.label)
            label_bmpdata = label.to_data(PixelFormat.bgra8, flip=True)
            label_icnsdata = label.to_data(PixelFormat.rgb8)
            label_png = label.convert(PixelFormat.rgb8).save()
            label_url = "data:image/png;base64," + base64.b64encode(label_png).decode()
        
        html_data = m.html_pod.find_named("src/shell.html").decode()
        html_data = html_data.replace("##js_file##", "%s.js" % basename)
        html_data = html_data.replace("##label_file##", label_url)
        
        html_path = path_join(path, "%s_html" % basename)
        dir_ensure_exists(html_path)
        file_write_text(path_join(html_path, "%s.html" % basename), html_data)
        file_write_text(path_join(html_path, "%s.js" % basename), m.js.text)
        
        html_path = path_join(path, "%s_wasm" % basename)
        dir_ensure_exists(html_path)
        file_write_text(path_join(html_path, "%s.html" % basename), html_data)
        file_write(path_join(html_path, "%s.wasm" % basename), m.html_pod.find_named("src/pico8_wasm.wasm"))
        file_write_text(path_join(html_path, "%s.js" % basename), m.wjs.text.replace("pico8_wasm.wasm", "%s.wasm" % basename))

        exe_data = m.bin_pod.find_named("bin/pico8.exe")
        if label_bmpdata:
            exe_icon_i = m.find_icon_offset_in_exe(exe_data)
            if e(exe_icon_i):
                exe_data = str_replace_at(exe_data, exe_icon_i, 0x10000, label_bmpdata)
            else:
                eprint("couldn't find icon in exe, not changing it")

        win_dir = "%s_windows" % basename
        with ZipFile(path_join(path, win_dir + ".zip"), "w") as win_zip:
            zip_write(win_zip, win_dir, "%s.exe" % basename, exe_data, exec=True)
            zip_write(win_zip, win_dir, "data.pod", m.pod.data)
            zip_write(win_zip, win_dir, "SDL2.dll", m.bin_pod.find_named("bin/SDL2.dll"))

        linux_dir = "%s_linux" % basename
        with ZipFile(path_join(path, linux_dir + ".zip"), "w") as linux_zip:
            zip_write(linux_zip, linux_dir, "data.pod", m.pod.data)
            if label_png: zip_write(linux_zip, linux_dir, "%s.png" % basename, label_png)
            zip_write(linux_zip, linux_dir, basename, m.bin_pod.find_named("bin/pico8_dyn.amd64"), exec=True)
        
        raspi_dir = "%s_raspi" % basename
        with ZipFile(path_join(path, raspi_dir + ".zip"), "w") as raspi_zip:
            zip_write(raspi_zip, raspi_dir, "data.pod", m.pod.data)
            if label_png: zip_write(raspi_zip, raspi_dir, "%s.png" % basename, label_png)
            for suffix, content in m.bin_pod.find_prefix("builds/pi_builds/pico8_player"):
                zip_write(raspi_zip, raspi_dir, basename + suffix, content, exec=True)

        if label_icnsdata:
            icns_data = m.create_icns_data(label_icnsdata) # doesn't seem to use "builds/osx_builds/pico8.icns" in the pod
        else:
            icns_data = m.bin_pod.find_named("builds/osx_builds/pico8.icns")

        # unfortunately, the plist template isn't in the pods - only in the exe. well, the exe's in the pod, so...
        info_plist = m.find_zstr(exe_data, b"<?xml", b"<key>CFBundleExecutable</key>")
        info_plist = info_plist.replace("%s.%s", "pico8_author.%s" % basename)
        info_plist = info_plist.replace("%s", basename)

        osx_dir = "%s.app" % basename
        with ZipFile(path_join(path, "%s_osx.zip" % basename), "w") as osx_zip:
            osx_cont_dir = zip_mkdir(osx_zip, osx_dir, "Contents")
            osx_mac_dir = zip_mkdir(osx_zip, osx_cont_dir, "MacOS")
            osx_res_dir = zip_mkdir(osx_zip, osx_cont_dir, "Resources")
            zip_write(osx_zip, osx_mac_dir, "data.pod", m.pod.data)
            zip_write(osx_zip, osx_mac_dir, basename, m.bin_pod.find_named("builds/osx_builds/pico8_player"), exec=True)
            zip_write(osx_zip, osx_res_dir, "%s.icns" % basename, icns_data)
            zip_write(osx_zip, osx_cont_dir, "Info.plist", info_plist.encode())

            osx_sdlfw_pod = PodFile(list(m.bin_pod.find_prefix("builds/osx_builds/sdl2_framework"))[0][1])
            osx_fw_dir = zip_mkdir(osx_zip, osx_cont_dir, "Frameworks")
            osx_sdlfw_dir = zip_mkdir(osx_zip, osx_fw_dir, "SDL2.framework")
            zip_copy(osx_zip, osx_sdlfw_dir, osx_sdlfw_pod, exclude="/_CodeSignature")
            osx_sdlver_dir = zip_mkdir(osx_zip, osx_sdlfw_dir, "Versions")
            zip_copy(osx_zip, zip_mkdir(osx_zip, osx_sdlver_dir, "Current"), osx_sdlfw_pod)
            zip_copy(osx_zip, zip_mkdir(osx_zip, osx_sdlver_dir, "A"), osx_sdlfw_pod)

def read_pod_file(path):
    return PodFile(file_read(path))

def read_cart_export(path, format):
    """Read a CartExport from the given path, assuming it is in the given format"""
    if format == CartFormat.js:
        return JsExport(file_read_text(path))
    if format == CartFormat.pod:
        return PodExport(file_read(path))
    else:
        throw(f"invalid format for listing: {format}")

def write_cart_export(path, export):
    """Write a CartExport to the given path"""
    if isinstance(export, JsExport):
        file_write_text(path, export.text)
    elif isinstance(export, PodExport):
        file_write(path, export.data)
    elif isinstance(export, FullExport):
        export.save(path)
    else:
        fail("invalid cart export")

def create_cart_export(format, pico8_dat, **opts):
    """Create an empty CartExport in the given format"""
    if format == CartFormat.js:
        return JsExport.create(pico8_dat, **opts)
    elif format == CartFormat.pod:
        return PodExport.create(pico8_dat, **opts)
    elif format == CartFormat.bin:
        return FullExport.create(pico8_dat, **opts)
    else:
        throw(f"invalid format for listing: {format}")

def read_from_cart_export(path, format, cart_name=None, extra_carts=None, **opts):
    """Read a cart or carts from a cart export"""
    export = read_cart_export(path, format)

    if e(extra_carts):
        assert not cart_name
        main_cart = None
        for cart in export.list_carts():
            if main_cart:
                extra_carts.append(export.read_cart(cart, **opts))
            else:
                main_cart = export.read_cart(cart, **opts)
        return main_cart
    else:
        return export.read_cart(cart_name, **opts)

def write_to_cart_export(path, cart, format, extra_carts=None, cart_name=None, target_name=None, cart_op=None, 
                         target_export=None, export_name=None, pico8_dat=None, **opts):
    """Create or edit a CartExport in the given path, depending on cart_op/cart_args arguments"""
    if not export_name:
        export_name = path_basename_no_extension(path)

    if cart_op is None:
        assert isinstance(pico8_dat, PodFile)
        export = create_cart_export(format, pico8_dat, cart=cart, export_name=export_name)
    else:
        assert isinstance(target_export, CartExport)
        export = target_export
        
    export.write_cart(cart, cart_name, cart_op, target_name, **opts)
    if extra_carts:
        for extra_cart in extra_carts:
            export.write_cart(extra_cart, **opts)
    
    write_cart_export(path, export)
