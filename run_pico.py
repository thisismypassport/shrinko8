from utils import *
from pico_defs import encode_p8str, decode_p8str, from_p8str, to_p8str, Memory
from pico_cart import read_cart_autodetect
from codecs import register as codec_register, CodecInfo

def _lupaz8_module():
    try:
        from lupaz8 import luaz8 # type: ignore
    except ImportError:
        throw("ERROR: You need lupaz8 (a fork of lupa) to execute pico8 scripts (do 'python -m pip install lupaz8')")
    return luaz8

k_p8_codec = CodecInfo(lambda i: (encode_p8str(i), len(i)), 
                       lambda i: (decode_p8str(i), len(i)))
def p8_codec_search(name):
    if name == "p8scii":
        return k_p8_codec
codec_register(p8_codec_search)

def picoscript_from_p8str(text, unicaps=False):
    return from_p8str(text, unicaps).encode() # encode to prevent encoding as p8str again

def picoscript_to_p8str(mess):
    return to_p8str(encode_p8str(mess).decode()) # mess is utf8 encoded as p8str, so must unmess first

def picoscript_to_memory(mess):
    return Memory(encode_p8str(mess))

def picoscript_print(val, *ignored):
    print(g_lupaz8_runtime.globals().tostr(val))

g_lupaz8_runtime = None
def get_runtime():
    global g_lupaz8_runtime
    if not g_lupaz8_runtime:
        g_lupaz8_runtime = _lupaz8_module().LuaRuntime(encoding="p8scii", source_encoding="p8scii")

        p8globs = g_lupaz8_runtime.globals()
        p8globs.print = picoscript_print
        p8globs.printh = picoscript_print
        
        shrinko = p8globs.shrinko = g_lupaz8_runtime.table()
        shrinko.from_p8str = picoscript_from_p8str
        shrinko.to_p8str = picoscript_to_p8str
        shrinko.to_memory = picoscript_to_memory
        
    return g_lupaz8_runtime

def exec_pico_code(code, *args):
    return get_runtime().execute(code, *args)

def exec_pico_script_by_path(path):
    cart = read_cart_autodetect(path) # for includes/etc
    
    result = get_runtime().execute(cart.code, name=path, mode='t')
    if not result:
        throw(f"ERROR: p8 script at {path} didn't return a module object")
    return result
