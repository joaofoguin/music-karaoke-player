from pathlib import Path
import sys

from PySide6.QtCore import QObject, Signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.playback_controller import PlaybackController


class FakeAudioEngine(QObject):
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()

    def __init__(self):
        super().__init__()
        self.calls = []
        self._position = 0
        self._duration = 0
        self._playing = False

    def load(self, path):
        self.calls.append(("load", path))

    def play(self):
        self.calls.append(("play",))
        self._playing = True
        self.playback_started.emit()

    def pause(self):
        self.calls.append(("pause",))
        self._playing = False
        self.playback_paused.emit()

    def stop(self):
        self.calls.append(("stop",))
        self._playing = False
        self.playback_stopped.emit()

    def set_position(self, position):
        self.calls.append(("set_position", position))
        self._position = position

    def set_volume(self, volume):
        self.calls.append(("set_volume", volume))

    def position(self):
        return self._position

    def duration(self):
        return self._duration

    def is_playing(self):
        return self._playing


def test_playback_controller_delegates_commands():
    engine = FakeAudioEngine()
    controller = PlaybackController(engine)

    controller.load(Path("song.mp3"))
    controller.play()
    controller.pause()
    controller.stop()
    controller.set_position(1500)
    controller.set_volume(80)

    assert engine.calls == [
        ("load", Path("song.mp3")),
        ("play",),
        ("pause",),
        ("stop",),
        ("set_position", 1500),
        ("set_volume", 80),
    ]
    assert controller.position() == 1500
    assert controller.is_playing() is False


def test_playback_controller_forwards_playback_signals():
    engine = FakeAudioEngine()
    controller = PlaybackController(engine)

    started = []
    paused = []
    stopped = []

    controller.playback_started.connect(lambda: started.append(True))
    controller.playback_paused.connect(lambda: paused.append(True))
    controller.playback_stopped.connect(lambda: stopped.append(True))

    controller.play()
    controller.pause()
    controller.stop()

    assert started == [True]
    assert paused == [True]
    assert stopped == [True]
