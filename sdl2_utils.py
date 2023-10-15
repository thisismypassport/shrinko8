from utils import *

# dummy file, without sdl2 dependency

class BlendMode(Enum):
    none = blend = ...

class Color(Tuple):
    r = g = b = ...; a = 0xff

    def set_a(m, a):
        return Color(m.r, m.g, m.b, a)

class PixelFormat(Enum):
    rgba8 = "RGBA"
    bgra8 = ("RGBA", "BGRA")
    rgb8 = "RGB"
    i8 = "P"

    @property
    def _pil_fmt(m):
        return m.value[0] if isinstance(m.value, tuple) else m.value
    @property
    def _pil_raw_fmt(m):
        return m.value[1] if isinstance(m.value, tuple) else m.value

    @property
    def bpp(m):
        if m == m.i8:
            return 8
        else:
            return 32

def _to_pil_tuple(obj):
    if obj is None:
        return None
    elif len(obj) == 2:
        return tuple(obj)
    elif len(obj) == 4:
        x, y, w, h = obj
        return x, y, x + w, y + h
    else:
        fail(obj)

def _pil_module():
    try:
        from PIL import Image # type: ignore
    except:
        throw("ERROR: You need pillow (or PIL) to read/write PNGs (do 'python -m pip install pillow')")
    return Image

class Surface:
    @staticmethod
    def load(f):
        return Surface(_pil_module().open(f))

    @staticmethod
    def create(w, h, fmt=PixelFormat.rgba8):
        return Surface(_pil_module().new(fmt._pil_fmt, (w, h)), fmt)
    
    @staticmethod
    def from_data(w, h, fmt, data, pitch=None):
        return Surface(_pil_module().frombytes(fmt._pil_fmt, (w, h), data, "raw", fmt._pil_raw_fmt, pitch or 0), fmt)

    def __init__(m, pil, fmt=None):
        m.pil = pil
        m.fmt = fmt
    
    def to_data(m, fmt=None, flip=False):
        if fmt is None:
            fmt = m.format
        return m.pil.tobytes("raw", fmt._pil_raw_fmt, 0, -1 if flip else 1)

    def save(m, dest=None):
        if dest is None:
            dest = BytesIO()
            m.save(dest)
            return dest.getvalue()
        
        m.pil.save(dest, "png")

    def convert(m, fmt):
        return Surface(m.pil.convert(fmt._pil_fmt))

    @property
    def width(m):
        return m.pil.width
    @property
    def height(m):
        return m.pil.height
    @property
    def size(m):
        return Point(m.width, m.height)
    
    @property
    def format(m):
        if m.fmt is None:
            m.fmt = PixelFormat(m.pil.mode)
        return m.fmt

    @property
    def pixels(m):
        return SurfacePixels(m.pil.load())

    def draw(m, src, dest=None, srcpos=None):
        src = src.pil.crop(_to_pil_tuple(srcpos)) if e(srcpos) else src
        m.pil.alpha_composite(src, _to_pil_tuple(dest))
    
    @writeonly_property
    def palette(m, pal):
        m.pil.putpalette(pal.raw, "RGBA")

class SurfacePixels:
    def __init__(m, pa):
        m.pa = pa
    
    def __getitem__(m, pos):
        return m.pa[pos]
    
    def __setitem__(m, pos, color):
        m.pa[pos] = color

class Palette: # (pil's ImagePalette doesn't seem fit for purpose)
    @staticmethod
    def create(n):
        return Palette([0] * (4 * n))

    def __init__(m, raw):
        m.raw = raw
    
    def __getitem__(m, i):
        return m.raw[4 * i : 4 * (i + 1)]
    
    def __setitem__(m, i, v):
        m.raw[4 * i : 4 * (i + 1)] = v
