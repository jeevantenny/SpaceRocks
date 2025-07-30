# -*- mode: python ; coding: utf-8 -*-


datas = [
    ('assets\\anim_controllers', 'assets\\anim_controllers'),
    ('assets\\animations', 'assets\\animations'),
    ('assets\\fonts', 'assets\\fonts'),
    ('assets\\sounds', 'assets\\sounds'),
    ('assets\\texture_maps', 'assets\\texture_maps'),
    ('assets\\textures', 'assets\\textures'),
    ('assets\\textures\\game_objects', 'assets\\textures\\game_objects'),
    ('assets\\textures\\ui', 'assets\\textures\\ui'),

    ('data', 'data'),
    ('user_data', 'user_data')
]


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
    debug=False,
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
