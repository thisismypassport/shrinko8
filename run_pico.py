#!/usr/bin/env python3
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

def picoscript_from_memory(bytearray):
    return bytes(bytearray)

def picoscript_to_fixnum(v):
    return float(v) / 0x10000

def picoscript_from_fixnum(v):
    v = int(v * 0x10000)
    if v < 0:
        v += 0x100000000
    return v

def picoscript_print(val, *_):
    print(g_globals.tostr(val))

def picoscript_printh(val, filename=None, overwrite=False, *_):
    val = g_globals.tostr(val)
    if not filename:
        eprint(val)
    elif overwrite:
        file_write_text(filename, val + "\n")
    else:
        file_append_text(filename, val + "\n")

def picoscript_stop(msg=None, *_):
    throw(g_globals.tostr(msg) if msg else "stop() called")

g_runtime = None
g_globals = None
def get_runtime():
    global g_runtime, g_globals
    if not g_runtime:
        g_runtime = _lupaz8_module().LuaRuntime(encoding="p8scii", source_encoding="p8scii",
                                                overflow_handler=True)
        g_globals = g_runtime.globals()

        g_globals.print = picoscript_print # to stdout
        g_globals.printh = picoscript_printh # to stderr or file
        g_globals.stop = picoscript_stop
        
        shrinko = g_globals.shrinko = g_runtime.table()
        shrinko.to_p8str = picoscript_to_p8str
        shrinko.from_p8str = picoscript_from_p8str
        shrinko.to_memory = picoscript_to_memory
        shrinko.from_memory = picoscript_from_memory
        shrinko.to_fixnum = picoscript_to_fixnum
        shrinko.from_fixnum = picoscript_from_fixnum

        # (would've added to lupaz8 except already released)
        python = g_globals.python
        python.attrs = python.as_attrgetter
        python.items = python.as_itemgetter
        
    return g_runtime

def exec_pico_code(code):
    return get_runtime().execute(code)

def exec_pico_script_by_path(path):
    cart = read_cart_autodetect(path) # for includes/etc
    
    result = get_runtime().execute(cart.code, name=path, mode='t')
    if not result:
        throw(f"ERROR: p8 script at {path} didn't return a module object")
    return result

g_pico_imports = {}
def import_pico_script(module_name):
    module = g_pico_imports.get(module_name)
    if module is None:
        path_pfx = module_name.replace(".", "/")
        for ext in [".lua", ".py"]:
            path = path_pfx + ext
            if path_exists(path):
                module = exec_pico_script_by_path(path)
                g_pico_imports[module_name] = module
                return module
        raise ModuleNotFoundError(module_name)
    return module

if __name__ == "__main__":
    arg = list_get(sys.argv, 1)
    if arg == "-c":
        exec_pico_code(list_get(sys.argv, 2))
    else:
        exec_pico_script_by_path(arg)
