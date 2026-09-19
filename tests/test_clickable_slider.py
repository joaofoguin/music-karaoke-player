from pathlib import Path
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.clickable_slider import ClickableSlider


def test_clickable_slider_creation():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    slider = ClickableSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 1000)
    slider.setValue(200)

    assert slider.value() == 200
    assert slider.maximum() == 1000
