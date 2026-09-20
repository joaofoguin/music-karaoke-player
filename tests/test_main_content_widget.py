import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from core.queue_controller import QueueController

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from widgets.main_content_widget import MainContentWidget


class FakeConfig:
    def __init__(self):
        self.values = {}

    def set(self, key, value):
        self.values[key] = value


def _app():
    return QApplication.instance() or QApplication([])


def test_main_content_widget_composes_explorer_queue_and_player():
    class FakeAudio(QObject):
        position_changed = Signal(int)
        playback_started = Signal()
        playback_paused = Signal()
        playback_stopped = Signal()
        position_changed = Signal(int)
        duration_changed = Signal(int)

        def set_position(self, _position):
            pass

    audio = FakeAudio()
    queue = QueueController()
    config = FakeConfig()

    _app()
    widget = MainContentWidget(audio, queue, [".mp3"], config)

    assert widget.explorer_widget is not None
    assert widget.queue_widget is not None
    assert widget.player_widget is not None
    assert widget.btn_add_arquivos is widget.queue_widget.btn_add_arquivos
    assert widget.botao_play is widget.player_widget.botao_play
    widget.deleteLater()


def test_main_content_widget_updates_audio_extensions():
    class FakeAudio(QObject):
        position_changed = Signal(int)
        playback_started = Signal()
        playback_paused = Signal()
        playback_stopped = Signal()
        duration_changed = Signal(int)

        def set_position(self, _position):
            pass

    _app()
    widget = MainContentWidget(FakeAudio(), QueueController(), [".mp3"], FakeConfig())

    widget.set_audio_extensions([".flac", ".ogg"])

    assert widget.audio_extensions == {".flac", ".ogg"}
    assert widget.explorer_widget.audio_extensions == {".flac", ".ogg"}
    widget.deleteLater()
