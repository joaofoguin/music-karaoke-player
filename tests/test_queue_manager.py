from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.track import Track
from core.queue_manager import QueueManager


def test_queue_manager_add_and_current():
    qm = QueueManager()
    assert qm.current() is None
    assert qm.current_index == -1

    t1 = Track(path=Path("song1.mp3"), title="Song 1")
    qm.add(t1)

    assert qm.current_index == 0
    assert qm.current() == t1
    assert len(qm.tracks) == 1

    t2 = Track(path=Path("song2.mp3"), title="Song 2")
    qm.add(t2)

    assert qm.current_index == 0
    assert len(qm.tracks) == 2


def test_queue_manager_navigation():
    qm = QueueManager()
    t1 = Track(path=Path("s1.mp3"), title="S1")
    t2 = Track(path=Path("s2.mp3"), title="S2")
    t3 = Track(path=Path("s3.mp3"), title="S3")

    for t in (t1, t2, t3):
        qm.add(t)

    assert qm.previous() is None  # Already at 0

    next_t = qm.next()
    assert next_t == t2
    assert qm.current_index == 1

    next_t = qm.next()
    assert next_t == t3
    assert qm.current_index == 2

    assert qm.next() is None  # End of queue

    prev_t = qm.previous()
    assert prev_t == t2
    assert qm.current_index == 1


def test_queue_manager_remove_and_move():
    qm = QueueManager()
    t1 = Track(path=Path("s1.mp3"), title="S1")
    t2 = Track(path=Path("s2.mp3"), title="S2")
    t3 = Track(path=Path("s3.mp3"), title="S3")

    for t in (t1, t2, t3):
        qm.add(t)

    qm.set_current(1)  # current is t2
    assert qm.current() == t2

    # Move t1 (index 0) to index 2
    success = qm.move(0, 2)
    assert success is True
    # Now order is: [t2, t3, t1]
    assert qm.tracks == [t2, t3, t1]
    assert qm.current_index == 0
    assert qm.current() == t2

    # Remove t3 (index 1)
    removed = qm.remove(1)
    assert removed == t3
    assert len(qm.tracks) == 2
    assert qm.current() == t2


def test_queue_manager_clear():
    qm = QueueManager()
    qm.add(Track(path=Path("s1.mp3"), title="S1"))
    assert len(qm.tracks) == 1
    qm.clear()
    assert len(qm.tracks) == 0
    assert qm.current_index == -1
    assert qm.current() is None
