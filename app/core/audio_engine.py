from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioEngine(QObject):
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()

    def __init__(self):
        super().__init__()

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()

        self.player.setAudioOutput(self.audio_output)

        self.player.positionChanged.connect(
            self.position_changed.emit
        )

        self.player.durationChanged.connect(
            self.duration_changed.emit
        )

        self.player.playbackStateChanged.connect(
            self._on_playback_state_changed
        )

        self.player.mediaStatusChanged.connect(
            self._on_media_status_changed
        )

    def load(self, path):
        url = QUrl.fromLocalFile(str(path))

        self.player.setSource(url)

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_position(self, position):
        self.player.setPosition(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)

    def position(self):
        return self.player.position()

    def duration(self):
        return self.player.duration()

    def is_playing(self):
        return (
            self.player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playback_started.emit()

        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.playback_paused.emit()

        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.playback_stopped.emit()

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished.emit()