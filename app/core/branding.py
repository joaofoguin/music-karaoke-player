from pathlib import Path
import sys

from PySide6.QtGui import QFont, QFontDatabase, QIcon


APP_NAME = "StageBox"
APP_VERSION_LABEL = "Beta"
APP_DISPLAY_NAME = f"{APP_NAME} ({APP_VERSION_LABEL})"


def resource_path(relative_path: str) -> Path:
    """Retorna o caminho de um recurso tanto no código-fonte quanto no executável."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base_path / relative_path


def load_branding(app) -> None:
    """Aplica identidade visual global da aplicação."""
    font_path = resource_path("assets/fonts/Poppins-Regular.ttf")
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        app.setFont(QFont("Poppins"))
    else:
        app.setFont(QFont("Poppins"))

    logo_path = resource_path("assets/logo.svg")
    if logo_path.is_file():
        app.setWindowIcon(QIcon(str(logo_path)))
