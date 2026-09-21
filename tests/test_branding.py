import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.branding import set_interface_font_size


def _app():
    return QApplication.instance() or QApplication([])


def test_set_interface_font_size_updates_application_font():
    app = _app()

    set_interface_font_size(app, 10.5)

    assert app.font().pointSizeF() == 10.5
