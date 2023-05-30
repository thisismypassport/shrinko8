from utils import *

# dummy file, without sdl2 dependency

class BlendMode(Enum):
    values = ("none", "blend")

class Color(Tuple):
    fields = ("r", "g", "b", "a")
    defaults = (0xff,)

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

class Surface:
    @staticmethod
    def _module():
        try:
            from PIL import Image # type: ignore
        except:
            raise ImportError("You need pillow (or PIL) to read/write PNGs (do 'python -m pip install pillow')")
        return Image

    @staticmethod
    def load(f):
        return Surface(Surface._module().open(f))

    @staticmethod
    def create(w, h):
        return Surface(Surface._module().new("RGBA", (w, h)))

    def __init__(m, pil):
        m.pil = pil

    def save(m, f):
        m.pil.save(f, "png")

    @property
    def width(m):
        return m.pil.width
    @property
    def height(m):
        return m.pil.height
    @property
    def size(m):
        return Point(m.width, m.height)

    def get_at(m, pos):
        return m.pa[pos]
    def set_at(m, pos, color):
        m.pa[pos] = color

    def lock(m):
        m.pa = m.pil.load()
    def unlock(m):
        m.pa = None

    def draw(m, src, dest=None, srcpos=None):
        src = src.pil.crop(_to_pil_tuple(srcpos)) if e(srcpos) else src
        m.pil.alpha_composite(src, _to_pil_tuple(dest))
