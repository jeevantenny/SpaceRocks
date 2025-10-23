# -*- mode: python ; coding: utf-8 -*-


data_paths = [
    "assets",

    "assets\\anim_controllers",
    "assets\\animations",
    "assets\\fonts",
    "assets\\texture_maps",
    "assets\\palette_swaps",

    "assets\\sounds\\entity\\asteroid",
    "assets\\sounds\\entity\\spaceship",
    "assets\\sounds\\game",

    "assets\\textures",
    "assets\\textures\\backgrounds",
    "assets\\textures\\game_objects",
    "assets\\textures\\ui",

    "data\\input_devices",
    "data\\levels"
]

datas = [(path, path) for path in data_paths]


a = Analysis( # type: ignore
    ['__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure) # type: ignore

exe = EXE( # type: ignore
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JJJ Asteroids',
    icon="assets/textures/exe_icon.ico",
    debug=True, # TODO Change this to False
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # TODO Change this to True
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # TODO Change this to False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
