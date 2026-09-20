from PySide6.QtCore import QObject, Signal

from core.audio_engine import AudioEngine


class PlaybackController(QObject):
    """Coordena os comandos de reprodução sem expor o backend de áudio à UI."""

    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()

    def __init__(self, audio_engine=None, parent=None):
        super().__init__(parent)

        self._audio_engine = audio_engine or AudioEngine()

        self._audio_engine.position_changed.connect(self.position_changed.emit)
        self._audio_engine.duration_changed.connect(self.duration_changed.emit)
        self._audio_engine.playback_started.connect(self.playback_started.emit)
        self._audio_engine.playback_paused.connect(self.playback_paused.emit)
        self._audio_engine.playback_stopped.connect(self.playback_stopped.emit)
        self._audio_engine.playback_finished.connect(self.playback_finished.emit)

    def load(self, path) -> None:
        """Carrega uma faixa sem iniciar sua reprodução."""
        self._audio_engine.load(path)

    def play(self) -> None:
        """Inicia ou retoma a reprodução."""
        self._audio_engine.play()

    def pause(self) -> None:
        """Pausa a reprodução atual."""
        self._audio_engine.pause()

    def stop(self) -> None:
        """Interrompe a reprodução atual."""
        self._audio_engine.stop()

    def set_position(self, position: int) -> None:
        """Define a posição atual da reprodução em milissegundos."""
        self._audio_engine.set_position(position)

    def set_volume(self, volume: int | float) -> None:
        """Define o volume usando a escala pública de 0 a 100."""
        self._audio_engine.set_volume(volume)

    def position(self) -> int:
        """Retorna a posição atual em milissegundos."""
        return self._audio_engine.position()

    def duration(self) -> int:
        """Retorna a duração da faixa em milissegundos."""
        return self._audio_engine.duration()

    def is_playing(self) -> bool:
        """Indica se o player está atualmente reproduzindo áudio."""
        return self._audio_engine.is_playing()
