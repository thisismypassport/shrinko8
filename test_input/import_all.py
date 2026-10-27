"""Validates that all py files can be imported before any others"""

from utils import *
import importlib, glob

our_dir = path_absolute(".")

our_modules = []
for entry in file_read_text("files.lst").split():
    for file in glob.glob(entry):
        if file.endswith(".py") and not path_dirname(file):
            our_modules.append(path_no_extension(file))
if not our_modules:
    raise Exception("something broken")

def delete_modules():
    deleted = {}
    all_modules = tuple(sys.modules.items())
    for modname, module in all_modules:
        modpath = getattr(module, "__file__", None)
        if modpath and modpath.startswith(our_dir):
            deleted[modname] = module
            del sys.modules[modname]
    if not deleted:
        raise Exception("delete_modules broken")
    return deleted

backup_modules = delete_modules()
for module_name in our_modules:
    try:
        importlib.import_module(module_name)
    except Exception:
        print(f"importing {module_name} failed")
        raise
    delete_modules()
sys.modules.update(backup_modules)
