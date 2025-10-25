# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
hidden_imports = ['pico_utils', 'scripts']
excludes = ['packaging']

import os
for script in os.listdir("scripts"):
    if script.endswith(".py") and script != "__init__.py":
        hidden_imports.append("scripts." + os.path.splitext(script)[0])

import pkgutil, PIL
for _, name, _ in pkgutil.walk_packages(PIL.__path__):
    if name.endswith("ImagePlugin") and name not in ("PngImagePlugin", "QoiImagePlugin"):
        excludes.append(f"{PIL.__name__}.{name}")

ana_p8 = Analysis(
    ['shrinko8.py'],
    pathex=[],
    binaries=[],
    datas=[('template.png', '.'), ('font.png', '.'), ('template.plist', '.')],
    hiddenimports=hidden_imports,
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
    datas=[('template64.png', '.'), ('font64.png', '.'), ('template.plist', '.')],
    hiddenimports=hidden_imports,
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
