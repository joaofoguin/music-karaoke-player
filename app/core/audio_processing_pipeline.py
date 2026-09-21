from PySide6.QtMultimedia import QAudioFormat

from core.audio_effects import AudioEffects
from core.audio_equalizer import AudioEqualizer
from core.audio_reverb import AudioReverbDelay
from core.pcm_converter import PcmConverter


class AudioProcessingPipeline:
    """Aplica efeitos PCM e entrega dados no formato exigido pela saída."""

    def __init__(self):
        self._pcm_converter = PcmConverter()
        self._equalizer = AudioEqualizer()
        self._equalizer_configuration = None
        self._reverb_delay = AudioReverbDelay()
        self._reverb_delay_configuration = None

    def reset(self):
        self._pcm_converter.reset()
        self._equalizer.reset()
        self._reverb_delay.reset()

    def process(
        self,
        data: bytes,
        source_format: QAudioFormat,
        target_format: QAudioFormat,
        mono_enabled: bool,
        normalize_enabled: bool,
        gain_db: float,
        noise_reduction_enabled: bool = False,
        noise_threshold_db: float = -45.0,
        noise_reduction_db: float = 18.0,
        equalizer_bass_db: float = 0.0,
        equalizer_mid_db: float = 0.0,
        equalizer_treble_db: float = 0.0,
        reverb_delay_enabled: bool = False,
        reverb_delay_ms: float = 120.0,
        reverb_feedback: float = 0.35,
        reverb_mix: float = 0.25,
    ) -> bytes:
        source_sample_format = self._sample_format_name(source_format.sampleFormat())
        if source_sample_format == "unknown":
            raise ValueError("Formato PCM de origem não suportado")

        processed = data
        channels = source_format.channelCount()

        if mono_enabled:
            processed = AudioEffects.mix_to_mono(
                processed, source_sample_format, channels
            )
            channels = 1
            if target_format.channelCount() > 1:
                processed = AudioEffects.mono_to_channels(
                    processed, source_sample_format, target_format.channelCount()
                )
                channels = target_format.channelCount()

        self._configure_equalizer(
            source_format.sampleRate(),
            channels,
            equalizer_bass_db,
            equalizer_mid_db,
            equalizer_treble_db,
        )
        processed = self._equalizer.process(
            processed, source_sample_format, channels
        )

        if reverb_delay_enabled:
            self._configure_reverb_delay(
                source_format.sampleRate(),
                channels,
                reverb_delay_ms,
                reverb_feedback,
                reverb_mix,
            )
            processed = self._reverb_delay.process(
                processed, source_sample_format, channels
            )

        if normalize_enabled:
            processed = AudioEffects.normalize_peak(
                processed, source_sample_format
            )

        if noise_reduction_enabled:
            processed = AudioEffects.apply_noise_reduction(
                processed,
                source_sample_format,
                noise_threshold_db,
                noise_reduction_db,
            )

        processed = AudioEffects.apply_gain(
            processed, source_sample_format, gain_db
        )

        effect_format = QAudioFormat(source_format)
        effect_format.setChannelCount(channels)

        if effect_format != target_format:
            processed = self._pcm_converter.convert(
                processed, effect_format, target_format
            )
        else:
            self._pcm_converter.reset()

        return processed

    def _configure_equalizer(
        self,
        sample_rate: int,
        channels: int,
        bass_db: float,
        mid_db: float,
        treble_db: float,
    ) -> None:
        configuration = (
            int(sample_rate),
            int(channels),
            float(bass_db),
            float(mid_db),
            float(treble_db),
        )
        if configuration == self._equalizer_configuration:
            return

        self._equalizer.configure(*configuration)
        self._equalizer_configuration = configuration

    def _configure_reverb_delay(
        self,
        sample_rate: int,
        channels: int,
        delay_ms: float,
        feedback: float,
        mix: float,
    ) -> None:
        configuration = (
            int(sample_rate),
            int(channels),
            float(delay_ms),
            float(feedback),
            float(mix),
        )
        if configuration == self._reverb_delay_configuration:
            return

        self._reverb_delay.configure(*configuration)
        self._reverb_delay_configuration = configuration

    @staticmethod
    def _sample_format_name(sample_format) -> str:
        mapping = {
            QAudioFormat.SampleFormat.UInt8: "uint8",
            QAudioFormat.SampleFormat.Int16: "int16",
            QAudioFormat.SampleFormat.Int32: "int32",
            QAudioFormat.SampleFormat.Float: "float32",
        }
        return mapping.get(sample_format, "unknown")
