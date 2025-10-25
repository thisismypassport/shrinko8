from utils import *
from media_utils import PixelFormat
from pico_defs import get_res_path
from picotron_cart import read_cart64_from_rom, write_cart64_to_rom, write_cart64, k_rom_header_sig, Cart64Format
from pico_export import FullExportBase
from zipfile import ZipFile
import base64

k_icon64_size = Point(128, 128)

class Cart64Export:
    """A picotron export"""

    # def get_cart(m, **opts)
    # def set_cart(m, cart, **opts)
    
    def dump_contents(m, dest, fmt, **_):
        throw("dumping misc. contents is only support for a .dat file")

class SysRom:
    """A picotron sysrom, used in both exports and in picotron.dat"""

    def __init__(m, data=None):
        m.entries = []
        if data:
            with BinaryReader(BytesIO(data), big_end=True) as r:
                while not r.eof():
                    size = r.u32()
                    entry = r.bytes(size)
                    m.entries.append(entry)

    class SysRomDir:
        def __init__(m, idx, entry):
            m.idx = idx
            m.files = read_cart64_from_rom(entry).files
        
        def get(m, name, strict=True):
            file = m.files.get(name)
            if not file:
                if strict:
                    throw(f"expected to find {name} in dat {m.idx} dir")
                else:
                    return None
            check(file.is_raw, "expected to find raw files inside dat dir")
            return file.data

    def get(m, idx, strict=True, dir=False):
        entry = list_get(m.entries, int(idx))
        if entry is None and strict:
            throw(f"expected to find {idx} in dat file")
        return m.SysRomDir(idx, entry) if dir else entry

    def set(m, idx, value):
        list_set(m.entries, int(idx), value, b"")

    def to_bytes(m):
        with BinaryWriter(big_end=True) as w:
            for entry in m.entries:
                w.u32(len(entry))
                w.bytes(entry)
            
            return w.f.getvalue()

    def dump_contents(m, dest, fmt, **_):
        cart_ext = f".{fmt}" if fmt.is_ext else ""
        for i, entry in enumerate(m.entries):
            is_cart = entry.startswith(k_rom_header_sig)
            path = path_join(dest, m.entry_name(i) + (cart_ext if is_cart else ""))

            if is_cart and fmt != Cart64Format.rom:
                write_cart64(path, read_cart64_from_rom(entry), fmt)
            else:
                file_write(path, entry)

class SysRomIndex(Enum):
    info = 0
    system = 1; cart = 2
    html_info = 3; linux_exe = 4
    win_exe = 5; win_sdl = 6
    mac_exe = 7; mac_sdl = 8

class SysRomExport64(SysRom, Cart64Export):
    def get_cart(m, **opts):
        entry = m.get(SysRomIndex.cart, strict=False)
        if not entry:
            throw("no cart in sysrom file")
        return read_cart64_from_rom(entry, **opts)

    def set_cart(m, cart, **opts):
        data = write_cart64_to_rom(cart, **opts)
        m.set(SysRomIndex.cart, data)
        
    def entry_name(m, i):
        try:
            return str(SysRomIndex(i))
        except ValueError:
            return f"unk{i}"
    
    @staticmethod
    def create(picotron_dat, cart=None, **_):
        m = SysRomExport64()
        m.set(SysRomIndex.info, cart.export_home.encode() if cart else b"")
        m.set(SysRomIndex.system, picotron_dat.get(SysRomIndex.cart))
        return m

class HtmlExport64(Cart64Export):
    def __init__(m, text):
        m.text = text

    def find_cart(m):
        match = re.search(r'p64cart_str="([0-9a-fA-F]*)"', m.text)
        if not match:
            throw("can't find p64cart_str var in html")
        return match

    def get_cart(m, **opts):
        match = m.find_cart()
        return read_cart64_from_rom(bytes.fromhex(match.group(1)), **opts)

    def set_cart(m, cart, **opts):
        rom = write_cart64_to_rom(cart, **opts)
        m.text = str_replace_between(m.text, *m.find_cart().span(1), rom.hex())

    @staticmethod
    def create(picotron_dat, cart=None, **_):
        html_info = picotron_dat.get(SysRomIndex.html_info, dir=True)
        html = html_info.get("shell.html").decode()
        js = html_info.get("picotron_player.js").decode()
        match = re.search(r'// ##pcart##\s+', html)
        if not match:
            throw("can't find pcart comment in html template")
        
        export_home = cart.export_home if cart else ""
        html = str_insert(html, match.end(), f'\np64cart_str="";\nexport_home_str = "{export_home}";\n{js}')

        title = list_get(cart.title, 0) if cart else None
        html = html.replace("##page_title##", title or "Picotron Cartridge")

        label = cart.load_label() if cart else None
        label_png = label.convert(PixelFormat.rgb8).save() if label else None
        if e(label_png):
            label_url = "data:image/png;base64," + base64.b64encode(label_png).decode()
            html = html.replace("##label_file##", label_url)

        return HtmlExport64(html)

class FullExport64(Cart64Export, FullExportBase):
    def __init__(m, picotron_dat):
        super().__init__()
        m.picotron_dat = picotron_dat

    @staticmethod
    def create(picotron_dat, export_name="", **opts):
        m = FullExport64(picotron_dat)
        m.export_name = export_name
        m.cart = None

        m.sysrom = SysRomExport64.create(picotron_dat, **opts)
        m.html = HtmlExport64.create(picotron_dat, **opts)
        m.exports = [m.sysrom, m.html]
        return m

    def set_cart(m, cart, **opts):
        m.cart = cart
        for export in m.exports:
            export.set_cart(cart, **opts)

    def zip_copy(m, zip, dir, datdir, exclude=None):
        for name, file in datdir.files.items():
            if not name.endswith(".info.pod"):
                if exclude and name.startswith(exclude):
                    continue

                exec = "." not in path_basename(name) # ???
                m.zip_write(zip, dir, name, default(file.data, b""), exec=exec, is_dir=file.is_dir)

    def save(m, path, delete_existing=False):
        dir_create(path, delete_existing=delete_existing)
        basename = m.export_name

        icon = m.cart.load_icon()
        if icon:
            icon = icon.resize(k_icon64_size)
            icon_bmpdata = icon.to_data(PixelFormat.bgra8, flip=True)
            icon_icnsdata = icon.to_data(PixelFormat.rgba8)
            icon_png = icon.convert(PixelFormat.rgba8).save()
        else:
            icon_bmpdata = icon_icnsdata = icon_png = None

        html_path = path_join(path, "%s.html" % basename)
        file_write_text(html_path, m.html.text)

        exe_data = m.picotron_dat.get(SysRomIndex.win_exe)
        if icon_bmpdata:
            exe_icon_i = m.find_icon_offset_in_exe(exe_data)
            if e(exe_icon_i):
                exe_data = str_replace_at(exe_data, exe_icon_i, 0x10000, icon_bmpdata)
            else:
                eprint("couldn't find icon in exe, not changing it")

        win_dir = "%s_windows" % basename
        with ZipFile(path_join(path, win_dir + ".zip"), "w") as win_zip:
            m.zip_write(win_zip, win_dir, "%s.exe" % basename, exe_data, exec=True)
            m.zip_write(win_zip, win_dir, "sysrom.dat", m.sysrom.to_bytes())
            m.zip_write(win_zip, win_dir, "SDL2.dll", m.picotron_dat.get(SysRomIndex.win_sdl))

        linux_dir = "%s_linux" % basename
        with ZipFile(path_join(path, linux_dir + ".zip"), "w") as linux_zip:
            m.zip_write(linux_zip, linux_dir, "sysrom.dat", m.sysrom.to_bytes())
            if icon_png: m.zip_write(linux_zip, linux_dir, "%s.png" % basename, icon_png)
            m.zip_write(linux_zip, linux_dir, basename, m.picotron_dat.get(SysRomIndex.linux_exe), exec=True)
        
        icns_data = m.create_icns_data(icon_icnsdata, has_alpha=True) if icon_icnsdata else None

        # unfortunately, the plist template isn't in the dats - only in the "real" exe (not even in the dat's exes...).
        info_plist = file_read_text(path_join(get_res_path(), "template.plist"))
        info_plist = info_plist.replace("%s.%s", "picotron_author.%s" % basename)
        info_plist = info_plist.replace("%s", basename)

        osx_dir = path_join("%s_mac" % basename, "%s.app" % basename)
        with ZipFile(path_join(path, "%s_mac.zip" % basename), "w") as osx_zip:
            osx_cont_dir = m.zip_mkdir(osx_zip, osx_dir, "Contents")
            osx_mac_dir = m.zip_mkdir(osx_zip, osx_cont_dir, "MacOS")
            osx_res_dir = m.zip_mkdir(osx_zip, osx_cont_dir, "Resources")
            m.zip_write(osx_zip, osx_mac_dir, "sysrom.dat", m.sysrom.to_bytes())
            m.zip_write(osx_zip, osx_mac_dir, basename, m.picotron_dat.get(SysRomIndex.mac_exe), exec=True)
            if icns_data: m.zip_write(osx_zip, osx_res_dir, "%s.icns" % basename, icns_data)
            m.zip_write(osx_zip, osx_cont_dir, "Info.plist", info_plist.encode())

            osx_sdl_indir = m.picotron_dat.get(SysRomIndex.mac_sdl, dir=True)
            osx_fw_dir = m.zip_mkdir(osx_zip, osx_cont_dir, "Frameworks")
            osx_sdlfw_dir = m.zip_mkdir(osx_zip, osx_fw_dir, "SDL2.framework")
            m.zip_copy(osx_zip, osx_sdlfw_dir, osx_sdl_indir, exclude="_CodeSignature")
            osx_sdlver_dir = m.zip_mkdir(osx_zip, osx_sdlfw_dir, "Versions")
            m.zip_copy(osx_zip, m.zip_mkdir(osx_zip, osx_sdlver_dir, "Current"), osx_sdl_indir)
            m.zip_copy(osx_zip, m.zip_mkdir(osx_zip, osx_sdlver_dir, "A"), osx_sdl_indir)

def read_sysrom_file(path):
    return SysRom(file_read(path))

def read_cart64_export(path, format):
    """Read a Cart64Export from the given path, assuming it is in the given format"""
    if format == Cart64Format.dat:
        return SysRomExport64(file_read(path))
    elif format == Cart64Format.html:
        return HtmlExport64(file_read_text(path))
    else:
        throw(f"invalid export format: {format}")

def write_cart64_export(path, export, delete_existing=False):
    """Write a CartExport to the given path"""
    if isinstance(export, SysRomExport64):
        file_write(path, export.to_bytes())
    elif isinstance(export, HtmlExport64):
        file_write_text(path, export.text)
    elif isinstance(export, FullExport64):
        export.save(path, delete_existing=delete_existing)
    else:
        fail("invalid cart export")

def create_cart64_export(format, pico_dat, **opts):
    """Create a Cart64Export in the given format"""
    if format == Cart64Format.dat:
        return SysRomExport64.create(pico_dat, **opts)
    elif format == Cart64Format.html:
        return HtmlExport64.create(pico_dat, **opts)
    elif format == Cart64Format.bin:
        return FullExport64.create(pico_dat, **opts)
    else:
        throw(f"invalid export format: {format}")

def write_to_cart64_export(path, cart, format, pico_dat=None, export_name=None, delete_existing=False, **opts):
    if not export_name:
        export_name = path_basename_no_extension(path)
    
    assert isinstance(pico_dat, SysRom)
    export = create_cart64_export(format, pico_dat, cart=cart, export_name=export_name)
    export.set_cart(cart, **opts)
    write_cart64_export(path, export, delete_existing)
