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

    converter = PcmConverter()
    result = converter.convert(data, source, target)

    assert struct.unpack("<2f", result) == (1.0, -1.0)


def test_pcm_converter_downmixes_channels():
    source = make_format(44100, 2, QAudioFormat.SampleFormat.Int16)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Int16)
    data = struct.pack("<4h", 1000, -2000, 3000, 5000)

    converter = PcmConverter()
    result = converter.convert(data, source, target)

    assert struct.unpack("<2h", result) == (-500, 4000)


def test_pcm_converter_resamples_frame_count():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(48000, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<4f", 0.0, 0.25, 0.5, 0.75)

    converter = PcmConverter()
    result = converter.convert(data, source, target)

    assert len(result) == round(4 * 48000 / 44100) * 4


def test_pcm_converter_keeps_resampling_phase_between_buffers():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(48000, 1, QAudioFormat.SampleFormat.Float)
    first = struct.pack("<4f", 0.0, 0.25, 0.5, 0.75)
    second = struct.pack("<4f", 1.0, 1.25, 1.5, 1.75)

    converter = PcmConverter()
    first_result = converter.convert(first, source, target)
    second_result = converter.convert(second, source, target)

    first_samples = struct.unpack("<%df" % (len(first_result) // 4), first_result)
    second_samples = struct.unpack("<%df" % (len(second_result) // 4), second_result)

    assert first_samples[-1] < second_samples[0]
    assert abs(second_samples[0] - 0.91875) < 0.01


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


def test_audio_processing_pipeline_applies_noise_reduction():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<2f", 0.005, 0.02)

    pipeline = AudioProcessingPipeline()
    result = pipeline.process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        noise_reduction_enabled=True,
        noise_threshold_db=-40.0,
        noise_reduction_db=20.0,
    )

    samples = struct.unpack("<2f", result)
    assert abs(samples[0] - 0.00275) < 1e-6
    assert abs(samples[1] - 0.02) < 1e-7


def test_audio_processing_pipeline_applies_equalizer():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<128f", *([0.1] * 128))

    pipeline = AudioProcessingPipeline()
    result = pipeline.process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )

    samples = struct.unpack("<128f", result)
    assert samples[-1] > 0.1


def test_audio_processing_pipeline_keeps_equalizer_state_between_buffers():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    samples = [0.1] * 256
    first = struct.pack("<128f", *samples[:128])
    second = struct.pack("<128f", *samples[128:])

    split_pipeline = AudioProcessingPipeline()
    split_first = split_pipeline.process(
        first,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )
    split_second = split_pipeline.process(
        second,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )

    single_pipeline = AudioProcessingPipeline()
    single = single_pipeline.process(
        struct.pack("<256f", *samples),
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )

    assert split_first + split_second == single


def test_audio_processing_pipeline_resets_equalizer_state():
    source = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(44100, 1, QAudioFormat.SampleFormat.Float)
    data = struct.pack("<128f", *([0.1] * 128))

    pipeline = AudioProcessingPipeline()
    pipeline.process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )
    pipeline.reset()
    after_reset = pipeline.process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )

    fresh = AudioProcessingPipeline().process(
        data,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        equalizer_bass_db=6.0,
    )

    assert after_reset == fresh


def test_audio_processing_pipeline_applies_reverb_delay_between_buffers():
    source = make_format(1000, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(1000, 1, QAudioFormat.SampleFormat.Float)
    first = struct.pack("<10f", *([0.0] * 9 + [1.0]))
    second = struct.pack("<10f", *([0.0] * 10))

    pipeline = AudioProcessingPipeline()
    first_result = pipeline.process(
        first,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        reverb_delay_enabled=True,
        reverb_delay_ms=10.0,
        reverb_feedback=0.0,
        reverb_mix=1.0,
    )
    second_result = pipeline.process(
        second,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        reverb_delay_ms=10.0,
        reverb_feedback=0.0,
        reverb_mix=1.0,
    )

    assert struct.unpack("<10f", first_result) == (0.0,) * 10
    second_samples = struct.unpack("<10f", second_result)
    assert second_samples[9] == 1.0
    assert all(
        sample == 0.0
        for index, sample in enumerate(second_samples)
        if index != 9
    )


def test_audio_processing_pipeline_resets_reverb_delay_state():
    source = make_format(1000, 1, QAudioFormat.SampleFormat.Float)
    target = make_format(1000, 1, QAudioFormat.SampleFormat.Float)
    first = struct.pack("<10f", *([0.0] * 9 + [1.0]))
    second = struct.pack("<10f", *([0.0] * 10))

    pipeline = AudioProcessingPipeline()
    pipeline.process(
        first,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        reverb_delay_ms=10.0,
        reverb_feedback=0.0,
        reverb_mix=1.0,
    )
    pipeline.reset()
    result = pipeline.process(
        second,
        source,
        target,
        mono_enabled=False,
        normalize_enabled=False,
        gain_db=0.0,
        reverb_delay_ms=10.0,
        reverb_feedback=0.0,
        reverb_mix=1.0,
    )

    assert struct.unpack("<10f", result) == (0.0,) * 10
