from utils import *

def run():
    from shrinko8 import main
    for lua_script in dir_paths("scripts"):
        if lua_script.endswith(".lua"):
            shutil.copy(lua_script, lua_script + ".bak.UNDO_BEFORE_PUSH")
            if main([lua_script, lua_script]) not in (0, None):
                raise Exception(f"prepackage - failed processing {lua_script}")

def unrun():
    for lua_script_bak in dir_paths("scripts"):
        if lua_script_bak.endswith(".lua.bak.UNDO_BEFORE_PUSH"):
            shutil.copy(lua_script_bak, path_no_extension(path_no_extension(lua_script_bak)))
            file_delete(lua_script_bak)

def build_wheel(*args, **kwargs):
    run()
    from setuptools.build_meta import build_wheel
    result = build_wheel(*args, **kwargs)
    unrun()
    return result

def build_sdist(*args, **kwargs):
    run()
    from setuptools.build_meta import build_sdist
    result = build_sdist(*args, **kwargs)
    unrun()
    return result

if __name__ == "__main__":
    if "-u" in sys.argv[1:]:
        unrun()
    else:
        run()
