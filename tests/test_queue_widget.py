import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.queue_controller import QueueController
from models.track import Track
from widgets.queue_widget import QueueWidget


def _app():
    return QApplication.instance() or QApplication([])


def _track(name):
    return Track(path=Path(name), title=Path(name).stem)


def test_queue_widget_renders_tracks_and_updates_on_queue_change():
    _app()
    controller = QueueController()
    widget = QueueWidget(controller)

    first = _track("song1.mp3")
    second = _track("song2.mp3")

    controller.add(first)
    assert widget.queue_layout.count() == 1
    assert widget.botao_limpar_fila.isEnabled()

    controller.add(second)
    assert widget.queue_layout.count() == 2

    controller.clear()
    assert widget.queue_layout.count() == 0
    assert not widget.botao_limpar_fila.isEnabled()


def test_queue_widget_emits_actions_from_queue_items():
    _app()
    controller = QueueController()
    widget = QueueWidget(controller)

    first = _track("song1.mp3")
    second = _track("song2.mp3")
    controller.add(first)
    controller.add(second)

    requested = []
    widget.play_requested.connect(lambda index: requested.append(("play", index)))
    widget.play_next_requested.connect(lambda index: requested.append(("next", index)))
    widget.move_requested.connect(lambda index, destination: requested.append(("move", index, destination)))
    widget.remove_requested.connect(lambda index: requested.append(("remove", index)))

    item = widget.queue_layout.itemAt(1).widget()
    item._on_play(1)
    item._on_play_next(1)
    item._on_move(1, 0)
    item._on_remove(1)

    assert requested == [
        ("play", 1),
        ("next", 1),
        ("move", 1, 0),
        ("remove", 1),
    ]


def test_queue_widget_refreshes_current_track_after_controller_selection():
    _app()
    controller = QueueController()
    widget = QueueWidget(controller)

    first = _track("song1.mp3")
    second = _track("song2.mp3")
    controller.add(first)
    controller.add(second)

    controller.set_current(1)

    current = widget.queue_layout.itemAt(1).widget()
    previous = widget.queue_layout.itemAt(0).widget()

    assert current.is_current is True
    assert previous.is_current is False
    assert current.is_next is False
