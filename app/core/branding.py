from pathlib import Path
import sys
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen


APP_NAME = "StageBox"
from .version import APP_VERSION

APP_VERSION_LABEL = "Beta"
APP_DISPLAY_NAME = f"{APP_NAME} ({APP_VERSION_LABEL})"
def _get_last_update() -> str:
    raw = os.environ.get("STAGEBOX_LAST_UPDATE", "")
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        except ValueError:
            pass
    return datetime.now().strftime("%d/%m/%Y")


APP_LAST_UPDATE = _get_last_update()


def resource_path(relative_path: str) -> Path:
    """Retorna o caminho de um recurso tanto no código-fonte quanto no executável."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base_path / relative_path


def set_interface_font_size(app, size: float) -> None:
    """Define o tamanho global da fonte da interface."""
    font = app.font()
    font.setPointSizeF(float(size))
    app.setFont(font)


def create_splash_screen() -> QSplashScreen:
    """Cria a tela inicial usando a arte final intro.svg."""
    intro_path = resource_path("assets/intro.svg")
    pixmap = QPixmap(str(intro_path))

    if pixmap.isNull():
        pixmap = QPixmap(620, 360)
        pixmap.fill(QColor("#0A0C10"))

    pixmap = pixmap.scaled(
        620,
        620,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    splash = QSplashScreen(pixmap, Qt.WindowType.FramelessWindowHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    return splash


def load_branding(app) -> None:
    """Aplica identidade visual global da aplicação."""
    font_path = resource_path("assets/fonts/Poppins-Regular.ttf")
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        app.setFont(QFont("Poppins"))

    logo_path = resource_path("assets/logo.svg")
    if logo_path.is_file():
        app.setWindowIcon(QIcon(str(logo_path)))
