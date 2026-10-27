"""Validates that all py files can be imported before any others"""

import sys, os, importlib

mydir = os.path.abspath(".")
def delete_modules():
    all_modules = tuple(sys.modules.items())
    for modname, module in all_modules:
        modpath = getattr(module, "__file__", None)
        if modpath and modpath.startswith(mydir):
            del sys.modules[modname]

for file in os.listdir("."):
    if file.endswith(".py"):
        try:
            importlib.import_module(os.path.splitext(file)[0])
        except Exception:
            print(f"importing {file} failed")
            raise
