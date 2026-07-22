# -*- mode: python ; coding: utf-8 -*-

import sys, os
sys.path.insert(0, os.path.abspath(SPECPATH))
from utils import *
import run_prepackage
import glob, pkgutil, PIL

block_cipher = None
excludes = {'packaging', 'setuptools', 'pkgutil', 'numpy'}
scripts = set()
datas = set()

run_prepackage.run()

for entry in file_read_text("files.lst").split():
    for file in glob.glob(entry):
        if file.endswith(".py"):
            modsplit = path_split_comps(path_no_extension(file))
            for i in range(len(modsplit) - 1):
                scripts.add(".".join(modsplit[:-1]))
            if modsplit[-1] != "__init__":
                scripts.add(".".join(modsplit))
        else:
            datas.add((file, path_dirname(file) or "."))

for _, name, _ in pkgutil.walk_packages(PIL.__path__):
    if name.endswith("ImagePlugin") and name not in ("PngImagePlugin", "QoiImagePlugin"):
        excludes.add(f"{PIL.__name__}.{name}")

excludes = list(excludes)
scripts = list(scripts)
datas = list(datas)

ana_p8 = Analysis(
    ['shrinko8.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=scripts,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)

ana_tron = Analysis(
    ['shrinkotron.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=scripts,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)

for ana in (ana_p8, ana_tron):
    ana.binaries = [bin for bin in ana.binaries if not bin[0].lower().startswith('api-ms-win-')]

pyz = PYZ(ana_p8.pure, ana_p8.zipped_data, cipher=block_cipher)

pyz_tron = PYZ(ana_tron.pure, ana_tron.zipped_data, cipher=block_cipher)

exe_p8 = EXE(
    pyz,
    ana_p8.dependencies,
    ana_p8.scripts,
    [],
    exclude_binaries=True,
    name='shrinko8',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon="pyinstaller.ico",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

exe_tron = EXE(
    pyz_tron,
    ana_tron.dependencies,
    ana_tron.scripts,
    [],
    exclude_binaries=True,
    name='shrinkotron',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon="pyinstaller.ico",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe_p8,
    ana_p8.binaries,
    ana_p8.zipfiles,
    ana_p8.datas,
    exe_tron,
    ana_tron.binaries,
    ana_tron.zipfiles,
    ana_tron.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='shrinko',
)

for license in dir_names("."):
    if license.startswith("LICENSE"):
        shutil.copy(license, path_join(DISTPATH, "shrinko"))

run_prepackage.unrun()
