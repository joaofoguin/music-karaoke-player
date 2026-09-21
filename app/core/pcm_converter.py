import struct
import sys

from PySide6.QtMultimedia import QAudioFormat


class PcmConverter:
    """Converte PCM intercalado entre formatos QAudioFormat."""

    _FORMATS = {
        QAudioFormat.SampleFormat.UInt8: ("B", 1, 127.0),
        QAudioFormat.SampleFormat.Int16: ("h", 2, 32767.0),
        QAudioFormat.SampleFormat.Int32: ("i", 4, 2147483647.0),
        QAudioFormat.SampleFormat.Float: ("f", 4, 1.0),
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self._resample_source_rate = None
        self._resample_target_rate = None
        self._resample_channels = None
        self._resample_phase = 0.0
        self._resample_previous_frame = None

    def convert(self, data: bytes, source_format: QAudioFormat, target_format: QAudioFormat) -> bytes:
        if source_format == target_format:
            return data

        source_info = self._FORMATS.get(source_format.sampleFormat())
        target_info = self._FORMATS.get(target_format.sampleFormat())
        if source_info is None or target_info is None:
            raise ValueError("Formato PCM não suportado para conversão")

        source_channels = source_format.channelCount()
        target_channels = target_format.channelCount()
        if source_channels <= 0 or target_channels <= 0:
            raise ValueError("Quantidade de canais inválida")

        source_samples = self._decode(data, source_format.sampleFormat())
        if len(source_samples) % source_channels:
            source_samples = source_samples[:len(source_samples) - (len(source_samples) % source_channels)]

        frames = [
            source_samples[index:index + source_channels]
            for index in range(0, len(source_samples), source_channels)
        ]
        frames = self._convert_channels(frames, target_channels)

        if source_format.sampleRate() != target_format.sampleRate():
            frames = self._resample(
                frames,
                source_format.sampleRate(),
                target_format.sampleRate(),
            )
        else:
            self.reset()

        samples = [sample for frame in frames for sample in frame]
        return self._encode(samples, target_format.sampleFormat())

    def _decode(self, data, sample_format):
        fmt = self._struct_format(sample_format)
        size = self._FORMATS[sample_format][1]
        count = len(data) // size
        return [
            self._to_float(struct.unpack_from(fmt, data, index * size)[0], sample_format)
            for index in range(count)
        ]

    def _encode(self, samples, sample_format):
        fmt = self._struct_format(sample_format)
        _, _, scale = self._FORMATS[sample_format]
        output = bytearray()
        for sample in samples:
            sample = max(-1.0, min(1.0, float(sample)))
            if sample_format == QAudioFormat.SampleFormat.UInt8:
                value = int(round(128.0 + sample * 127.0))
                value = max(0, min(255, value))
            elif sample_format == QAudioFormat.SampleFormat.Float:
                value = sample
            else:
                value = int(round(sample * scale))
                limits = {
                    QAudioFormat.SampleFormat.Int16: (-32768, 32767),
                    QAudioFormat.SampleFormat.Int32: (-2147483648, 2147483647),
                }
                low, high = limits[sample_format]
                value = max(low, min(high, value))
            output.extend(struct.pack(fmt, value))
        return bytes(output)

    @classmethod
    def _struct_format(cls, sample_format):
        fmt = cls._FORMATS[sample_format][0]
        return ("<" if sys.byteorder == "little" else ">") + fmt

    @staticmethod
    def _to_float(value, sample_format):
        if sample_format == QAudioFormat.SampleFormat.UInt8:
            return (value - 128.0) / 127.0
        if sample_format == QAudioFormat.SampleFormat.Int16:
            return value / 32767.0
        if sample_format == QAudioFormat.SampleFormat.Int32:
            return value / 2147483647.0
        return float(value)

    @staticmethod
    def _convert_channels(frames, target_channels):
        if not frames:
            return frames

        source_channels = len(frames[0])
        if source_channels == target_channels:
            return frames
        if target_channels == 1:
            return [[sum(frame) / source_channels] for frame in frames]
        if source_channels == 1:
            return [[frame[0]] * target_channels for frame in frames]

        converted = []
        for frame in frames:
            if target_channels < source_channels:
                converted.append([
                    sum(frame[channel::target_channels]) / len(frame[channel::target_channels])
                    for channel in range(target_channels)
                ])
            else:
                converted.append([
                    frame[channel] if channel < source_channels else frame[-1]
                    for channel in range(target_channels)
                ])
        return converted

    def _resample(self, frames, source_rate, target_rate):
        if not frames or source_rate <= 0 or target_rate <= 0:
            return frames
        if source_rate == target_rate:
            self.reset()
            return frames

        channels = len(frames[0])
        state = (source_rate, target_rate, channels)
        if state != (
            self._resample_source_rate,
            self._resample_target_rate,
            self._resample_channels,
        ):
            self.reset()
            self._resample_source_rate = source_rate
            self._resample_target_rate = target_rate
            self._resample_channels = channels

        if self._resample_previous_frame is not None:
            frames = [self._resample_previous_frame] + frames

        ratio = source_rate / target_rate
        position = self._resample_phase
        last_index = len(frames) - 1
        result = []

        while position < last_index:
            left = int(position)
            right = min(last_index, left + 1)
            fraction = position - left
            result.append([
                frames[left][channel] * (1.0 - fraction)
                + frames[right][channel] * fraction
                for channel in range(channels)
            ])
            position += ratio

        self._resample_previous_frame = frames[-1]
        self._resample_phase = position - last_index
        return result
