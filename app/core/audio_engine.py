from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import (
    QAudioBufferOutput,
    QAudioFormat,
    QAudioSink,
    QAudioOutput,
    QMediaDevices,
    QMediaPlayer,
)

from core.audio_processing_pipeline import AudioProcessingPipeline


class AudioEngine(QObject):
    """Encapsula a reprodução de áudio, saída nativa e efeitos PCM."""

    VOLUME_MAX = 100

    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()
    output_device_changed = Signal(str)
    mono_changed = Signal(bool)
    gain_changed = Signal(float)
    normalize_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.media_devices = QMediaDevices(self)
        self._configured_output_device_id = ""
        self._mono_enabled = False
        self._gain_db = 0.0
        self._normalize_enabled = False
        self._buffer_callback_count = 0
        self._audio_pipeline = AudioProcessingPipeline()

        default_device = self.media_devices.defaultAudioOutput()
        self.audio_output = QAudioOutput(default_device, self)
        self.audio_output.setMuted(False)
        self.audio_output.setVolume(1.0)

        self._buffer_output = QAudioBufferOutput(self)
        self._buffer_output.audioBufferReceived.connect(self._on_audio_buffer_received)
        self._audio_sink = None
        self._sink_io = None
        self._sink_format = None
        self._audio_pipeline.reset()
        self._processed_output_device = default_device

        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.position_changed.emit)
        self.player.durationChanged.connect(self.duration_changed.emit)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_error)
        self.media_devices.audioOutputsChanged.connect(self._on_audio_outputs_changed)

    def load(self, path: Path | str) -> None:
        self.player.setSource(QUrl.fromLocalFile(str(path)))

    def play(self) -> None:
        self.player.play()

    def pause(self) -> None:
        self.player.pause()

    def stop(self) -> None:
        self.player.stop()
        self._reset_processed_output()

    def set_position(self, position: int) -> None:
        if self._processing_enabled():
            self._reset_processed_output()
        self.player.setPosition(position)

    def set_volume(self, volume: int | float) -> None:
        normalized = max(0.0, min(1.0, volume / self.VOLUME_MAX))
        self.audio_output.setVolume(normalized)
        if self._audio_sink is not None:
            self._audio_sink.setVolume(normalized)

    def output_devices(self):
        return self.media_devices.audioOutputs()

    def set_configured_output_device_id(self, device_id: str) -> None:
        self._configured_output_device_id = device_id or ""

    def output_device_id(self) -> str:
        device = self._processed_output_device if self._processing_enabled() else self.audio_output.device()
        return bytes(device.id()).hex() if not device.isNull() else ""

    def set_output_device(self, device_id: str) -> bool:
        if not device_id:
            device = self.media_devices.defaultAudioOutput()
        else:
            device = next(
                (item for item in self.media_devices.audioOutputs()
                 if bytes(item.id()).hex() == device_id),
                None,
            )
        if device is None or device.isNull():
            return False

        current = self._current_output_device()
        if not current.isNull() and bytes(current.id()) == bytes(device.id()):
            return True

        was_playing = self.is_playing()
        current_position = self.player.position()
        if was_playing:
            self.player.pause()

        if self._processing_enabled():
            self._recreate_processed_output(device)
        else:
            self.audio_output.setDevice(device)

        if was_playing:
            self.player.setPosition(current_position)
            self.player.play()

        self.output_device_changed.emit(device.description())
        return True

    def set_gain_db(self, gain_db: float) -> None:
        gain_db = float(gain_db)
        if gain_db == self._gain_db:
            return

        was_playing = self.is_playing()
        current_position = self.player.position()
        if was_playing:
            self.player.pause()

        self._gain_db = gain_db
        if self._processing_enabled():
            self._enable_processed_output()
        else:
            self._disable_processed_output()

        if was_playing:
            self.player.setPosition(current_position)
            self.player.play()

        self.gain_changed.emit(gain_db)

    def gain_db(self) -> float:
        return self._gain_db

    def set_normalize_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._normalize_enabled:
            return

        was_playing = self.is_playing()
        current_position = self.player.position()
        if was_playing:
            self.player.pause()

        self._normalize_enabled = enabled
        if self._processing_enabled():
            self._enable_processed_output()
        else:
            self._disable_processed_output()

        if was_playing:
            self.player.setPosition(current_position)
            self.player.play()

        self.normalize_changed.emit(enabled)

    def normalize_enabled(self) -> bool:
        return self._normalize_enabled

    def _processing_enabled(self) -> bool:
        return (
            self._mono_enabled
            or self._gain_db != 0.0
            or self._normalize_enabled
        )

    def set_mono_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._mono_enabled:
            return

        was_playing = self.is_playing()
        current_position = self.player.position()
        if was_playing:
            self.player.pause()

        self._mono_enabled = enabled
        if enabled:
            self._buffer_callback_count = 0
            self._enable_processed_output()
        else:
            if self._processing_enabled():
                self._enable_processed_output()
            else:
                self._disable_processed_output()

        if was_playing:
            self.player.setPosition(current_position)
            self.player.play()

        self.mono_changed.emit(enabled)

    def mono_enabled(self) -> bool:
        return self._mono_enabled

    def position(self) -> int:
        return self.player.position()

    def duration(self) -> int:
        return self.player.duration()

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _current_output_device(self):
        return self._processed_output_device if self._processing_enabled() else self.audio_output.device()

    def _enable_processed_output(self) -> None:
        device = self.audio_output.device()
        self.player.setAudioOutput(self.audio_output)
        self.player.setAudioBufferOutput(self._buffer_output)
        self.audio_output.setMuted(True)
        self._recreate_processed_output(device)

    def _disable_processed_output(self) -> None:
        self._reset_processed_output()
        self.player.setAudioBufferOutput(None)
        self.audio_output.setMuted(False)
        self.player.setAudioOutput(self.audio_output)

    def _configure_buffer_output(self, device) -> None:
        # O QAudioBufferOutput não depende do dispositivo de saída.
        # Mantemos a mesma instância para não interromper o vínculo com o player
        # durante uma troca de modo ou de dispositivo.
        return

    def _recreate_processed_output(self, device) -> None:
        self._reset_processed_output()
        self._pending_sink_device = device
        self._processed_output_device = device
        self._configure_buffer_output(device)
        if self._processing_enabled():
            self.player.setAudioBufferOutput(self._buffer_output)

    def _on_audio_buffer_received(self, buffer) -> None:
        if not self._processing_enabled() or not buffer.isValid():
            return

        self._buffer_callback_count += 1
        if self._buffer_callback_count == 1:
            print("Pipeline de efeitos: QAudioBufferOutput recebeu o primeiro buffer PCM")

        source_format = buffer.format()
        channel_count = source_format.channelCount()
        if channel_count <= 0:
            return

        output_format = QAudioFormat(source_format)
        if self._audio_sink is None or self._sink_format != output_format:
            self._reset_processed_output(keep_pending_device=True)
            device = getattr(self, "_pending_sink_device", self.media_devices.defaultAudioOutput())
            if device.isNull():
                return

            if not device.isFormatSupported(output_format):
                preferred = device.preferredFormat()
                if preferred.isValid():
                    output_format = preferred
                else:
                    print("Efeito de áudio indisponível: dispositivo sem formato de saída válido")
                    return

            self._sink_format = output_format
            self._audio_sink = QAudioSink(device, output_format, self)
            self._audio_sink.setVolume(self.audio_output.volume())

        raw_data = bytes(buffer.constData())
        try:
            processed = self._audio_pipeline.process(
                raw_data,
                source_format,
                output_format,
                self._mono_enabled,
                self._normalize_enabled,
                self._gain_db,
            )
        except ValueError as exc:
            print(f"Efeito de áudio indisponível: {exc}")
            return

        # Escreve diretamente na QIODevice interna do QAudioSink.
        # Isso evita que um QIODevice intermediário retorne zero bytes entre
        # dois buffers do decoder e coloque o sink em IdleState.
        if self._sink_io is None:
            self._sink_io = self._audio_sink.start()
            if self._sink_io is None:
                print("Efeito de áudio indisponível: não foi possível iniciar a saída PCM")
                return

        written = self._sink_io.write(processed)
        if written < 0:
            print(
                f"Erro ao enviar PCM mono para a saída: "
                f"estado={self._audio_sink.state()}, erro={self._audio_sink.error()}"
            )
        elif written != len(processed):
            print(
                f"Saída PCM mono aceitou apenas {written} de "
                f"{len(processed)} bytes"
            )

    def _on_sink_state_changed(self, state) -> None:
        if self._audio_sink is None:
            return
        if self._audio_sink.error().value != 0:
            print(
                f"Erro na saída PCM mono: estado={state}, "
                f"erro={self._audio_sink.error()}"
            )

    def _reset_processed_output(self, keep_pending_device: bool = False) -> None:
        if self._audio_sink is not None:
            self._audio_sink.reset()
            self._audio_sink.stop()
            self._audio_sink.deleteLater()
            self._audio_sink = None

        self._sink_io = None
        self._sink_format = None

        if not keep_pending_device:
            self._pending_sink_device = self._current_output_device()

    def _on_audio_outputs_changed(self) -> None:
        configured_id = getattr(self, "_configured_output_device_id", "")
        if configured_id:
            selected = next(
                (item for item in self.media_devices.audioOutputs()
                 if bytes(item.id()).hex() == configured_id),
                None,
            )
            if selected is not None and not selected.isNull():
                if self._current_output_device().id() != selected.id():
                    self._switch_output_device(selected)
                return

        new_device = self.media_devices.defaultAudioOutput()
        if new_device.isNull():
            return

        current_device = self._current_output_device()
        if not current_device.isNull() and current_device.id() == new_device.id():
            return

        self._switch_output_device(new_device)

    def _switch_output_device(self, new_device) -> None:
        was_playing = self.is_playing()
        current_position = self.player.position()
        if was_playing:
            self.player.pause()

        if self._processing_enabled():
            self._recreate_processed_output(new_device)
        else:
            self.audio_output.setDevice(new_device)

        if was_playing:
            self.player.setPosition(current_position)
            self.player.play()

        self.output_device_changed.emit(new_device.description())

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
