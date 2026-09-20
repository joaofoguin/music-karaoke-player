from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.queue_controller import QueueController
from core.queue_manager import QueueManager
from models.track import Track


def _track(name):
    return Track(path=Path(name), title=Path(name).stem)


def test_queue_controller_delegates_queue_operations():
    manager = QueueManager()
    controller = QueueController(manager)

    first = _track("song1.mp3")
    second = _track("song2.mp3")
    third = _track("song3.mp3")

    controller.add(first)
    controller.add(second)
    controller.add(third)

    assert controller.tracks == [first, second, third]
    assert controller.current_index == 0
    assert controller.current() == first

    assert controller.set_current(1) == second
    assert controller.next() == third
    assert controller.previous() == second

    assert controller.move(0, 2) is True
    assert controller.tracks == [second, third, first]
    assert controller.current_index == 0

    assert controller.set_play_next(2) is True
    assert controller.tracks == [second, first, third]

    assert controller.remove(1) == first
    assert controller.tracks == [second, third]

    controller.clear()
    assert controller.tracks == []
    assert controller.current_index == -1
    assert controller.current() is None


def test_queue_controller_forwards_state_signals():
    controller = QueueController()

    queue_changes = []
    current_changes = []

    controller.queue_changed.connect(lambda: queue_changes.append(True))
    controller.current_changed.connect(lambda track: current_changes.append(track))

    first = _track("song1.mp3")
    second = _track("song2.mp3")

    controller.add(first)
    controller.add(second)
    controller.set_current(1)
    controller.previous()
    controller.remove(0)
    controller.clear()

    assert len(queue_changes) == 4
    assert current_changes[0] == first
    assert current_changes[1] == first
    assert current_changes[2] == second
    assert current_changes[3] == first
    assert current_changes[4] == first
    assert current_changes[5] is None
