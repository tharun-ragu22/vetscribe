# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for VetScribe Assistant.
#
# Builds a --onedir (folder) distribution rather than a single --onefile
# binary: AV vendors are much more likely to flag a self-extracting onefile
# executable as a false positive, which would block clinics from installing
# the app at all.
#
# Build with:
#   uv run pyinstaller build_spec/vetscribe.spec --distpath dist --workpath build

from pathlib import Path

repo_root = Path(SPECPATH).parent
src_dir = repo_root / "src"

block_cipher = None

a = Analysis(
    [str(src_dir / "vetscribe" / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VetScribe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VetScribe",
)
