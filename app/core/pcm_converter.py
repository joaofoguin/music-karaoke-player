import math
import struct

from PySide6.QtMultimedia import QAudioFormat


class PcmConverter:
    """Converte PCM intercalado entre formatos QAudioFormat."""

    _FORMATS = {
        QAudioFormat.SampleFormat.UInt8: ("<B", 1, 128.0, 127.0),
        QAudioFormat.SampleFormat.Int16: ("<h", 2, 0.0, 32767.0),
        QAudioFormat.SampleFormat.Int32: ("<i", 4, 0.0, 2147483647.0),
        QAudioFormat.SampleFormat.Float: ("<f", 4, 0.0, 1.0),
    }

    @classmethod
    def convert(cls, data: bytes, source_format: QAudioFormat, target_format: QAudioFormat) -> bytes:
        if source_format == target_format:
            return data

        source_info = cls._FORMATS.get(source_format.sampleFormat())
        target_info = cls._FORMATS.get(target_format.sampleFormat())
        if source_info is None or target_info is None:
            raise ValueError("Formato PCM não suportado para conversão")

        source_channels = source_format.channelCount()
        target_channels = target_format.channelCount()
        if source_channels <= 0 or target_channels <= 0:
            raise ValueError("Quantidade de canais inválida")

        source_samples = cls._decode(data, source_format.sampleFormat())
        if len(source_samples) % source_channels:
            source_samples = source_samples[:len(source_samples) - (len(source_samples) % source_channels)]

        frames = [
            source_samples[index:index + source_channels]
            for index in range(0, len(source_samples), source_channels)
        ]
        frames = cls._convert_channels(frames, target_channels)

        if source_format.sampleRate() != target_format.sampleRate():
            frames = cls._resample(
                frames,
                source_format.sampleRate(),
                target_format.sampleRate(),
            )

        samples = [sample for frame in frames for sample in frame]
        return cls._encode(samples, target_format.sampleFormat())

    @classmethod
    def _decode(cls, data, sample_format):
        fmt = cls._FORMATS[sample_format][0]
        size = cls._FORMATS[sample_format][1]
        count = len(data) // size
        return [
            cls._to_float(struct.unpack_from(fmt, data, index * size)[0], sample_format)
            for index in range(count)
        ]

    @classmethod
    def _encode(cls, samples, sample_format):
        fmt, _, offset, scale = cls._FORMATS[sample_format]
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

    @staticmethod
    def _resample(frames, source_rate, target_rate):
        if not frames or source_rate <= 0 or target_rate <= 0:
            return frames
        if source_rate == target_rate:
            return frames

        output_count = max(1, round(len(frames) * target_rate / source_rate))
        result = []
        max_index = len(frames) - 1
        for output_index in range(output_count):
            position = output_index * source_rate / target_rate
            left = min(max_index, int(math.floor(position)))
            right = min(max_index, left + 1)
            fraction = position - left
            result.append([
                frames[left][channel] * (1.0 - fraction)
                + frames[right][channel] * fraction
                for channel in range(len(frames[0]))
            ])
        return result
