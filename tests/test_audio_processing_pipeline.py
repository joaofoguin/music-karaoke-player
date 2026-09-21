from pathlib import Path
import struct
import sys

from PySide6.QtMultimedia import QAudioFormat

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.audio_processing_pipeline import AudioProcessingPipeline
from core.pcm_converter import PcmConverter


def make_format(rate, channels, sample_format):
    fmt = QAudioFormat()
    fmt.setSampleRate(rate)
    fmt.setChannelCount(channels)
    fmt.setSampleFormat(sample_format)
    return fmt


def test_pcm_converter_int16_to_float32():
    source = make_format(44100, 2, QAudioFormat.SampleFormat.Int16)
    target = make_format(44100, 2, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<2h", 32767, -32767)

    result = PcmConverter.convert(data, source, target)

    assert struct.unpack("<2f", result) == (1.0, -1.0)


def test_pcm_converter_downmixes_channels():
    source = make_format(44100, 2, QAudioFormat.SampleFormat.Int16)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Int16)
    data = struct.pack("<4h", 1000, -2000, 3000, 5000)

    result = PcmConverter.convert(data, source, target)

    assert struct.unpack("<2h", result) == (-500, 4000)


def test_pcm_converter_resamples_frame_count():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(48000, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<4f", 0.0, 0.25, 0.5, 0.75)

    result = PcmConverter.convert(data, source, target)

    assert len(result) == 4 * 48000 // 44100 * 4 or len(result) == round(4 * 48000 / 44100) * 4


def test_audio_processing_pipeline_outputs_target_format():
    source = make_format(44100, 2, QAudioFormat.SampleFormat.Int16)
    target = make_format(48000, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<4h", 1000, -2000, 3000, 5000)

    pipeline = AudioProcessingPipeline()
    result = pipeline.process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
    )

    assert len(result) == round(2 * 48000 / 44100) * 4
    samples = struct.unpack("<%df" % (len(result) // 4), result)
    assert all(-1.0 <= sample <= 1.0 for sample in samples)


def test_audio_processing_pipeline_applies_gain_before_conversion():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Int16)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<h", 8192)

    pipeline = AudioProcessingPipeline()
    result = pipeline.process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=6.0206,
    )

    sample = struct.unpack("<f", result)[0]
    assert abs(sample - (16384 / 32767.0)) < 1e-5
