# -*- mode: python ; coding: utf-8 -*-
import os, zipfile

os.makedirs('build', exist_ok=True)
_zip_path = os.path.join('build', 'preview_images.zip')
with zipfile.ZipFile(_zip_path, 'w', compression=zipfile.ZIP_STORED) as _zf:
    for _cat in ('cards', 'uniques'):
        _dir = os.path.join('preview_images', _cat)
        if os.path.isdir(_dir):
            for _fn in sorted(os.listdir(_dir)):
                _fp = os.path.join(_dir, _fn)
                if os.path.isfile(_fp):
                    _zf.write(_fp, f'{_cat}/{_fn}')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icons', 'icons_default'), ('names_ru.json', '.'), ('prices_cache.json', '.'), ('leagues.json', '.'), ('items_preview.json', '.'), (_zip_path, '.')],
    hiddenimports=['pystray._win32', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UltimatumOverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.ico'],
)
