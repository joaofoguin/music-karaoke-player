from pathlib import Path
import sys

from PySide6.QtCore import QObject, Signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.playback_coordinator import PlaybackCoordinator
from core.queue_controller import QueueController
from models.track import Track


class FakePlaybackController(QObject):
    playback_finished = Signal()

    def __init__(self):
        super().__init__()
        self.calls = []
        self._playing = False
        self._position = 0

    def load(self, path):
        self.calls.append(("load", path))

    def play(self):
        self.calls.append(("play",))
        self._playing = True

    def pause(self):
        self.calls.append(("pause",))
        self._playing = False

    def set_position(self, position):
        self.calls.append(("set_position", position))
        self._position = position

    def is_playing(self):
        return self._playing


def track(name):
    return Track(path=Path(name), title=Path(name).stem)


def test_playback_coordinator_select_and_navigation():
    playback = FakePlaybackController()
    queue = QueueController()
    coordinator = PlaybackCoordinator(playback, queue)

    first = track("first.mp3")
    second = track("second.mp3")
    third = track("third.mp3")
    for item in (first, second, third):
        queue.add(item)

    changed = []
    coordinator.track_changed.connect(changed.append)

    assert coordinator.select_and_play(0) == first
    assert coordinator.next() == second
    assert coordinator.previous() == first

    assert changed == [first, second, first]
    assert playback.calls == [
        ("load", first.path),
        ("play",),
        ("load", second.path),
        ("play",),
        ("load", first.path),
        ("play",),
    ]


def test_playback_coordinator_previous_restarts_before_navigating():
    playback = FakePlaybackController()
    queue = QueueController()
    coordinator = PlaybackCoordinator(playback, queue)

    queue.add(track("first.mp3"))
    queue.add(track("second.mp3"))
    coordinator.select(1)

    coordinator.previous()
    assert queue.current_index == 1
    assert playback.calls[-1] == ("set_position", 0)

    coordinator.previous()
    assert queue.current_index == 0


def test_playback_coordinator_handles_repeat_and_queue_end():
    playback = FakePlaybackController()
    queue = QueueController()
    coordinator = PlaybackCoordinator(playback, queue)

    first = track("first.mp3")
    second = track("second.mp3")
    queue.add(first)
    queue.add(second)
    coordinator.select(0)

    coordinator.repeat = True
    coordinator.handle_finished()
    assert queue.current() == first
    assert playback.calls[-2:] == [("load", first.path), ("play",)]

    coordinator.repeat = False
    ended = []
    coordinator.playback_finished_at_end.connect(lambda: ended.append(True))

    coordinator.handle_finished()
    assert queue.current() == second
    assert playback.calls[-2:] == [("load", second.path), ("play",)]

    coordinator.handle_finished()
    assert queue.current() == second
    assert ended == [True]
