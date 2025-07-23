# -*- mode: python ; coding: utf-8 -*-


a = Analysis( # type: ignore
    ['__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets\\anim_controllers', 'assets\\anim_controllers'),
        ('assets\\animations', 'assets\\animations'),
        ('assets\\fonts', 'assets\\fonts'),
        ('assets\\sounds', 'assets\\sounds'),
        ('assets\\texture_maps', 'assets\\texture_maps'),
        ('assets\\textures\\game_objects', 'assets\\textures\\game_objects'),
        ('assets\\textures\\ui', 'assets\\textures\\ui'),

        ('data', 'data')
    ],
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
    name='__main__',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # TODO Change This to False
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # TODO Change This to True
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
