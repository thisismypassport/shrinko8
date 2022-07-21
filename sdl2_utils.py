from utils import *

# dummy file, without sdl2 dependency

class BlendMode(Enum):
    values = ("none", "blend")

class Color(Tuple):
    fields = ("r", "g", "b", "a")
    defaults = (0xff,)

class Surface:
    @staticmethod
    def load():
        raise Exception("this is not supported in this git")
        
