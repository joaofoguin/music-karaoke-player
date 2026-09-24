from PySide6.QtCore import QObject, Signal

from core.playback_controller import PlaybackController
from core.queue_controller import QueueController


class PlaybackCoordinator(QObject):
    """Orquestra fila e reprodução sem depender dos widgets da interface."""

    track_changed = Signal(object)
    playback_finished_at_end = Signal()

    def __init__(
        self,
        playback_controller=None,
        queue_controller=None,
        parent=None,
    ):
        super().__init__(parent)
        self.playback = (
            playback_controller
            if playback_controller is not None
            else PlaybackController()
        )
        self.queue = (
            queue_controller
            if queue_controller is not None
            else QueueController()
        )
        self.repeat = False
        self._previous_restarted = False

        self.playback.playback_finished.connect(self.handle_finished)

    def select(self, index: int):
        track = self.queue.set_current(index)
        if track is None:
            return None

        self._previous_restarted = False
        self.playback.load(track.path)
        self.track_changed.emit(track)
        return track

    def select_and_play(self, index: int):
        track = self.select(index)
        if track is not None:
            self.playback.play()
        return track

    def play_current(self):
        track = self.queue.current()
        if track is not None:
            self.playback.play()
        return track

    def toggle_playback(self):
        track = self.queue.current()
        if track is None:
            return None

        if self.playback.is_playing():
            self.playback.pause()
        else:
            self.playback.play()
        return track

    def previous(self):
        if not self._previous_restarted:
            self.playback.set_position(0)
            self._previous_restarted = True
            return self.queue.current()

        track = self.queue.previous()
        if track is None:
            self.playback.set_position(0)
            self._previous_restarted = False
            return None

        self._previous_restarted = False
        self.playback.load(track.path)
        self.track_changed.emit(track)
        self.playback.play()
        return track

    def next(self):
        # Após avançar, o primeiro clique em anterior deve reiniciar a faixa atual.
        self._previous_restarted = False
        track = self.queue.next()
        if track is None:
            return None

        self.playback.load(track.path)
        self.track_changed.emit(track)
        self.playback.play()
        return track

    def handle_finished(self):
        if self.repeat:
            track = self.queue.current()
            if track is not None:
                self.playback.load(track.path)
                self.playback.play()
            return

        track = self.queue.next()
        if track is None:
            self.playback_finished_at_end.emit()
            return

        self._previous_restarted = False
        self.playback.load(track.path)
        self.track_changed.emit(track)
        self.playback.play()
