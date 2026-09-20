from PySide6.QtCore import QObject, Signal

from core.queue_manager import QueueManager


class QueueController(QObject):
    """Coordena operações da fila sem expor o gerenciador à interface."""

    queue_changed = Signal()
    current_changed = Signal(object)

    def __init__(self, queue_manager=None, parent=None):
        super().__init__(parent)
        self._queue_manager = queue_manager if queue_manager is not None else QueueManager()

    @property
    def tracks(self):
        return self._queue_manager.tracks

    @property
    def current_index(self):
        return self._queue_manager.current_index

    def add(self, track):
        self._queue_manager.add(track)
        self.queue_changed.emit()
        self.current_changed.emit(self.current())

    def remove(self, index):
        removed = self._queue_manager.remove(index)
        if removed is not None:
            self.queue_changed.emit()
            self.current_changed.emit(self.current())
        return removed

    def clear(self):
        self._queue_manager.clear()
        self.queue_changed.emit()
        self.current_changed.emit(None)

    def move(self, index, destination):
        moved = self._queue_manager.move(index, destination)
        if moved:
            self.queue_changed.emit()
            self.current_changed.emit(self.current())
        return moved

    def set_play_next(self, index):
        moved = self._queue_manager.set_play_next(index)
        if moved:
            self.queue_changed.emit()
            self.current_changed.emit(self.current())
        return moved

    def current(self):
        return self._queue_manager.current()

    def set_current(self, index):
        track = self._queue_manager.set_current(index)
        if track is not None:
            self.current_changed.emit(track)
        return track

    def previous(self):
        track = self._queue_manager.previous()
        if track is not None:
            self.current_changed.emit(track)
        return track

    def next(self):
        track = self._queue_manager.next()
        if track is not None:
            self.current_changed.emit(track)
        return track
