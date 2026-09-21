from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


PROJECT_DIR = Path(SPECPATH)
APP_DIR = PROJECT_DIR / "app"

# PySide6 carrega módulos dinamicamente em alguns pontos da aplicação.
hiddenimports = collect_submodules("PySide6.QtMultimedia")

a = Analysis(
    [str(APP_DIR / "main.py")],
    pathex=[str(APP_DIR)],
    binaries=[],
    datas=[
        (str(PROJECT_DIR / "assets"), "assets"),
    ],
    icon=str(PROJECT_DIR / "assets" / "logo.png"),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="StageBox-Beta",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
