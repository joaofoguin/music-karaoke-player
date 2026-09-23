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
APP_LAST_UPDATE = os.environ.get("STAGEBOX_LAST_UPDATE", datetime.now().strftime("%d/%m/%Y"))


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
    """Cria a tela inicial exibida enquanto o StageBox carrega."""
    pixmap = QPixmap(620, 360)
    pixmap.fill(QColor("#0A0C10"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    logo_path = resource_path("assets/logo.svg")
    logo = QPixmap(str(logo_path))
    if not logo.isNull():
        logo = logo.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap((pixmap.width() - logo.width()) // 2, 48, logo)

    title_font = QFont("Poppins", 24)
    title_font.setWeight(QFont.Weight.DemiBold)
    painter.setFont(title_font)
    painter.setPen(QColor("#F3F4F6"))
    painter.drawText(pixmap.rect().adjusted(0, 208, 0, -92), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, APP_DISPLAY_NAME)

    version_font = QFont("Poppins", 10)
    painter.setFont(version_font)
    painter.setPen(QColor("#9CA3AF"))
    painter.drawText(pixmap.rect().adjusted(0, 266, 0, -54), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, f"Versão {APP_VERSION}")

    painter.setPen(QColor("#6B7280"))
    painter.drawText(pixmap.rect().adjusted(0, 316, 0, -20), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "Carregando...")
    painter.end()

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
