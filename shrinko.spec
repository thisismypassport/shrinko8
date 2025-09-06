# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
hidden_imports = ['pico_utils']
excludes = ['packaging']
TODO::scripts/*

ana = Analysis(
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

pyz = PYZ(ana.pure, ana.zipped_data, cipher=block_cipher)

pyz_tron = PYZ(ana_tron.pure, ana_tron.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    ana.dependencies,
    ana.scripts,
    [],
    exclude_binaries=True,
    name='shrinko8',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    ana.binaries,
    ana.zipfiles,
    ana.datas,
    exe_tron,
    ana_tron.binaries,
    ana_tron.zipfiles,
    ana_tron.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='shrinko',
)
