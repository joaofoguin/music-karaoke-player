import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from widgets.main_content_widget import MainContentWidget


class FakeConfig:
    def __init__(self):
        self.values = {}

    def set(self, key, value):
        self.values[key] = value


def _app():
    return QApplication.instance() or QApplication([])


def test_main_content_widget_composes_explorer_queue_and_player(qtbot):
    class FakeAudio:
        from PySide6.QtCore import QObject, Signal
        position_changed = Signal(int)

    class FakeQueue:
        pass

    audio = FakeAudio()
    queue = FakeQueue()
    config = FakeConfig()

    _app()
    widget = MainContentWidget(audio, queue, [".mp3"], config)
    qtbot.addWidget(widget)

    assert widget.explorer_widget is not None
    assert widget.queue_widget is not None
    assert widget.player_widget is not None
    assert widget.btn_add_arquivos is widget.queue_widget.btn_add_arquivos
    assert widget.botao_play is widget.player_widget.botao_play


def test_main_content_widget_updates_audio_extensions(qtbot):
    class FakeAudio:
        from PySide6.QtCore import QObject, Signal
        position_changed = Signal(int)

    class FakeQueue:
        pass

    _app()
    widget = MainContentWidget(FakeAudio(), FakeQueue(), [".mp3"], FakeConfig())
    qtbot.addWidget(widget)

    widget.set_audio_extensions([".flac", ".ogg"])

    assert widget.audio_extensions == {".flac", ".ogg"}
    assert widget.explorer_widget.audio_extensions == {".flac", ".ogg"}
