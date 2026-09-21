from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules\nfrom PIL import Image


PROJECT_DIR = Path(SPECPATH)
APP_DIR = PROJECT_DIR / "app"

# O Windows espera um ícone ICO para o executável.\nicon_png = PROJECT_DIR / "assets" / "logo.png"\nicon_ico = PROJECT_DIR / "assets" / "logo.ico"\nif icon_png.exists():\n    with Image.open(icon_png) as image:\n        image.convert("RGBA").save(icon_ico, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64)])\n\n# PySide6 carrega módulos dinamicamente em alguns pontos da aplicação.
hiddenimports = collect_submodules("PySide6.QtMultimedia")

a = Analysis(
    [str(APP_DIR / "main.py")],
    pathex=[str(APP_DIR)],
    binaries=[],
    datas=[
        (str(PROJECT_DIR / "assets"), "assets"),
    ],
    icon=str(icon_ico),
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
