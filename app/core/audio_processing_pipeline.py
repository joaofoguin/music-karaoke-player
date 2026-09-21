from PySide6.QtMultimedia import QAudioFormat

from core.audio_effects import AudioEffects
from core.pcm_converter import PcmConverter


class AudioProcessingPipeline:
    """Aplica efeitos PCM e entrega dados no formato exigido pela saída."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._source_format = None
        self._target_format = None

    def process(
        self,
        data: bytes,
        source_format: QAudioFormat,
        target_format: QAudioFormat,
        mono_enabled: bool,
        normalize_enabled: bool,
        gain_db: float,
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

        if normalize_enabled:
            processed = AudioEffects.normalize_peak(
                processed, source_sample_format
            )

        processed = AudioEffects.apply_gain(
            processed, source_sample_format, gain_db
        )

        effect_format = QAudioFormat(source_format)
        effect_format.setChannelCount(channels)

        if effect_format != target_format:
            processed = PcmConverter.convert(
                processed, effect_format, target_format
            )

        return processed

    @staticmethod
    def _sample_format_name(sample_format) -> str:
        mapping = {
            QAudioFormat.SampleFormat.UInt8: "uint8",
            QAudioFormat.SampleFormat.Int16: "int16",
            QAudioFormat.SampleFormat.Int32: "int32",
            QAudioFormat.SampleFormat.Float: "float32",
        }
        return mapping.get(sample_format, "unknown")
