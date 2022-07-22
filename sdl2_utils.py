from utils import *

# dummy file, without sdl2 dependency

class BlendMode(Enum):
    values = ("none", "blend")

class Color(Tuple):
    fields = ("r", "g", "b", "a")
    defaults = (0xff,)

class Surface:
    @staticmethod
    def load(f):
        try:
            from PIL import Image # type: ignore
        except:
            raise Exception("You need pillow (or PIL) for this")
        return Surface(Image.open(f))

    def __init__(m, pil):
        m.pil = pil

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

    def lock(m):
        m.pa = m.pil.load()
    def unlock(m):
        m.pa = None
        
