from PySide6.QtCore import QObject, Signal

from core.audio_backend import AudioBackend
from core.audio_engine import AudioEngine


class PlaybackController(QObject):
    """Coordena os comandos de reprodução sem expor o backend de áudio à UI."""

    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()

    def __init__(self, audio_engine: AudioBackend | None = None, parent=None):
        super().__init__(parent)

        self._audio_engine: AudioBackend = audio_engine if audio_engine is not None else AudioEngine()

        self._audio_engine.position_changed.connect(self.position_changed.emit)
        self._audio_engine.duration_changed.connect(self.duration_changed.emit)
        self._audio_engine.playback_started.connect(self.playback_started.emit)
        self._audio_engine.playback_paused.connect(self.playback_paused.emit)
        self._audio_engine.playback_stopped.connect(self.playback_stopped.emit)
        self._audio_engine.playback_finished.connect(self.playback_finished.emit)

    def load(self, path) -> None:
        self._audio_engine.load(path)

    def play(self) -> None:
        self._audio_engine.play()

    def pause(self) -> None:
        self._audio_engine.pause()

    def stop(self) -> None:
        self._audio_engine.stop()

    def set_position(self, position: int) -> None:
        self._audio_engine.set_position(position)

    def set_volume(self, volume: int | float) -> None:
        self._audio_engine.set_volume(volume)

    def output_devices(self):
        return self._audio_engine.output_devices()

    def output_device_id(self) -> str:
        return self._audio_engine.output_device_id()

    def set_output_device(self, device_id: str) -> bool:
        return self._audio_engine.set_output_device(device_id)

    def set_configured_output_device_id(self, device_id: str) -> None:
        self._audio_engine.set_configured_output_device_id(device_id)

    def set_mono_enabled(self, enabled: bool) -> None:
        self._audio_engine.set_mono_enabled(enabled)

    def mono_enabled(self) -> bool:
        return self._audio_engine.mono_enabled()

    def set_gain_db(self, gain_db: float) -> None:
        self._audio_engine.set_gain_db(gain_db)

    def gain_db(self) -> float:
        return self._audio_engine.gain_db()

    def set_normalize_enabled(self, enabled: bool) -> None:
        self._audio_engine.set_normalize_enabled(enabled)

    def normalize_enabled(self) -> bool:
        return self._audio_engine.normalize_enabled()

    def set_noise_reduction_enabled(self, enabled: bool) -> None:
        self._audio_engine.set_noise_reduction_enabled(enabled)

    def noise_reduction_enabled(self) -> bool:
        return self._audio_engine.noise_reduction_enabled()

    def set_noise_reduction_settings(self, threshold_db: float, reduction_db: float) -> None:
        self._audio_engine.set_noise_reduction_settings(threshold_db, reduction_db)

    def noise_threshold_db(self) -> float:
        return self._audio_engine.noise_threshold_db()

    def noise_reduction_db(self) -> float:
        return self._audio_engine.noise_reduction_db()

    def position(self) -> int:
        return self._audio_engine.position()

    def duration(self) -> int:
        return self._audio_engine.duration()

    def is_playing(self) -> bool:
        return self._audio_engine.is_playing()
