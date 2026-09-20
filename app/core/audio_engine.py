from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QAudioDevice, QMediaDevices, QMediaPlayer


class AudioEngine(QObject):
    """Encapsula a reprodução de áudio e sua saída nativa do Qt."""

    VOLUME_MAX = 100

    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()

    def __init__(self):
        super().__init__()

        default_device = QMediaDevices.defaultAudioOutput()
        self.audio_output = QAudioOutput(default_device)
        self.audio_output.setMuted(False)
        self.audio_output.setVolume(1.0)

        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        self.player.positionChanged.connect(self.position_changed.emit)
        self.player.durationChanged.connect(self.duration_changed.emit)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_error)

    def load(self, path: Path | str) -> None:
        """Carrega uma faixa sem iniciar sua reprodução."""
        self.player.setSource(QUrl.fromLocalFile(str(path)))

    def play(self) -> None:
        """Inicia ou retoma a reprodução."""
        self.player.play()

    def pause(self) -> None:
        """Pausa a reprodução atual."""
        self.player.pause()

    def stop(self) -> None:
        """Interrompe a reprodução atual."""
        self.player.stop()

    def set_position(self, position: int) -> None:
        """Define a posição atual da reprodução em milissegundos."""
        self.player.setPosition(position)

    def set_volume(self, volume: int | float) -> None:
        """Define o volume usando a escala pública de 0 a 100."""
        self.audio_output.setVolume(volume / self.VOLUME_MAX)

    def position(self) -> int:
        """Retorna a posição atual em milissegundos."""
        return self.player.position()

    def duration(self) -> int:
        """Retorna a duração da faixa em milissegundos."""
        return self.player.duration()

    def is_playing(self) -> bool:
        """Indica se o player está atualmente reproduzindo áudio."""
        return (
            self.player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )

    def _on_playback_state_changed(self, state) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playback_started.emit()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.playback_paused.emit()
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.playback_stopped.emit()

    def _on_media_status_changed(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished.emit()

    def _on_error(self, error, error_string) -> None:
        if error != QMediaPlayer.Error.NoError:
            print(f"Erro de reprodução: {error_string}")
