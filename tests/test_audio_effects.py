from pathlib import Path
import sys
import struct

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.audio_effects import AudioEffects
from core.audio_equalizer import AudioEqualizer


def test_mix_to_mono_int16_average_channels():
    data = struct.pack("<4h", 1000, -2000, 3000, 5000)
    result = AudioEffects.mix_to_mono(data, "int16", 2)
    assert struct.unpack("<2h", result) == (-500, 4000)


def test_mix_to_mono_float32_average_channels():
    data = struct.pack("<4f", 1.0, -0.5, 0.25, 0.75)
    result = AudioEffects.mix_to_mono(data, "float32", 2)
    assert struct.unpack("<2f", result) == (0.25, 0.5)


def test_mix_to_mono_uint8_average_channels():
    data = bytes([0, 255, 10, 30])
    result = AudioEffects.mix_to_mono(data, "uint8", 2)
    assert result == bytes([128, 20])


def test_mono_to_channels_int16():
    data = struct.pack("<2h", 1000, -2000)
    result = AudioEffects.mono_to_channels(data, "int16", 2)
    assert struct.unpack("<4h", result) == (1000, 1000, -2000, -2000)


def test_mono_to_channels_float32():
    data = struct.pack("<2f", 0.25, -0.5)
    result = AudioEffects.mono_to_channels(data, "float32", 2)
    assert struct.unpack("<4f", result) == (0.25, 0.25, -0.5, -0.5)


def test_mix_to_mono_keeps_mono_data_unchanged():
    data = struct.pack("<2h", 100, -200)
    assert AudioEffects.mix_to_mono(data, "int16", 1) == data


def test_mix_to_mono_rejects_unknown_format():
    try:
        AudioEffects.mix_to_mono(b"\x00\x00", "unknown", 2)
    except ValueError as exc:
        assert "Formato PCM não suportado" in str(exc)
    else:
        raise AssertionError("Era esperado ValueError")


def test_apply_gain_int16():
    data = struct.pack("<3h", 1000, -1000, 30000)
    result = AudioEffects.apply_gain(data, "int16", 6.0206)
    samples = struct.unpack("<3h", result)
    assert samples[0] == 2000
    assert samples[1] == -2000
    assert samples[2] == 32767


def test_apply_gain_float32():
    data = struct.pack("<2f", 0.25, -0.5)
    result = AudioEffects.apply_gain(data, "float32", 6.0206)
    assert struct.unpack("<2f", result) == (0.5, -1.0)


def test_apply_gain_zero_keeps_data():
    data = struct.pack("<2h", 100, -200)
    assert AudioEffects.apply_gain(data, "int16", 0) == data


def test_normalize_peak_float32():
    data = struct.pack("<3f", 0.25, -0.5, 0.75)
    result = AudioEffects.normalize_peak(data, "float32")
    samples = struct.unpack("<3f", result)
    assert abs(samples[0] - 0.297083646) < 1e-6
    assert abs(samples[1] + 0.594167292) < 1e-6
    assert abs(samples[2] - 0.891250938) < 1e-6


def test_normalize_peak_int16():
    data = struct.pack("<3h", 1000, -2000, 16000)
    result = AudioEffects.normalize_peak(data, "int16")
    samples = struct.unpack("<3h", result)
    assert samples[2] in range(29202, 29206)


def test_normalize_peak_silence_keeps_data():
    data = struct.pack("<3h", 0, 0, 0)
    assert AudioEffects.normalize_peak(data, "int16") == data


def test_normalize_peak_rejects_invalid_target():
    try:
        AudioEffects.normalize_peak(b"\x00\x00", "int16", 0)
    except ValueError as exc:
        assert "Pico-alvo inválido" in str(exc)
    else:
        raise AssertionError("Era esperado ValueError")


def test_apply_noise_reduction_float32_attenuates_low_level_signal():
    data = struct.pack("<3f", 0.005, 0.02, -0.005)
    result = AudioEffects.apply_noise_reduction(
        data, "float32", threshold_db=-40.0, reduction_db=20.0
    )
    samples = struct.unpack("<3f", result)
    assert abs(samples[0] - 0.00275) < 1e-6
    assert abs(samples[1] - 0.02) < 1e-7
    assert abs(samples[2] + 0.00275) < 1e-6


def test_apply_noise_reduction_zero_reduction_keeps_data():
    data = struct.pack("<2f", 0.005, -0.002)
    assert AudioEffects.apply_noise_reduction(
        data, "float32", threshold_db=-40.0, reduction_db=0.0
    ) == data


def test_apply_noise_reduction_rejects_invalid_parameters():
    data = struct.pack("<f", 0.001)
    for threshold, reduction in [(-90.0, 18.0), (-45.0, 70.0)]:
        try:
            AudioEffects.apply_noise_reduction(
                data, "float32", threshold_db=threshold, reduction_db=reduction
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Era esperado ValueError")


def test_equalizer_zero_gain_keeps_float32_data():
    data = struct.pack("<4f", 0.1, -0.2, 0.3, -0.4)
    equalizer = AudioEqualizer()
    equalizer.configure(44100, 1)
    assert equalizer.process(data, "float32", 1) == data


def test_equalizer_boost_changes_signal():
    data = struct.pack("<128f", *([0.1] * 128))
    equalizer = AudioEqualizer()
    equalizer.configure(44100, 1, bass_db=6.0)
    result = equalizer.process(data, "float32", 1)
    samples = struct.unpack("<128f", result)
    assert samples[-1] > 0.1


def test_equalizer_preserves_state_between_buffers():
    samples = [0.1] * 256
    first = struct.pack("<128f", *samples[:128])
    second = struct.pack("<128f", *samples[128:])

    split_equalizer = AudioEqualizer()
    split_equalizer.configure(44100, 1, bass_db=6.0)
    split_result = split_equalizer.process(first, "float32", 1) + split_equalizer.process(
        second, "float32", 1
    )

    single_equalizer = AudioEqualizer()
    single_equalizer.configure(44100, 1, bass_db=6.0)
    single_result = single_equalizer.process(
        struct.pack("<256f", *samples), "float32", 1
    )

    assert split_result == single_result


def test_equalizer_supports_stereo_pcm():
    data = struct.pack("<4h", 1000, -1000, 2000, -2000)
    equalizer = AudioEqualizer()
    equalizer.configure(44100, 2, mid_db=3.0)
    result = equalizer.process(data, "int16", 2)
    assert len(result) == len(data)


def test_equalizer_rejects_invalid_configuration():
    equalizer = AudioEqualizer()
    for sample_rate, channels, gain in [(0, 1, 0.0), (44100, 0, 0.0), (44100, 1, 13.0)]:
        try:
            equalizer.configure(
                sample_rate,
                channels,
                bass_db=gain,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Era esperado ValueError")


from core.audio_reverb import AudioReverbDelay


def test_reverb_delay_applies_delayed_signal():
    effect = AudioReverbDelay()
    effect.configure(1000, 1, delay_ms=10.0, feedback=0.0, mix=1.0)

    first = struct.pack("<10f", *([0.0] * 9 + [1.0]))
    second = struct.pack("<10f", *([0.0] * 10))

    first_result = effect.process(first, "float32", 1)
    second_result = effect.process(second, "float32", 1)

    assert struct.unpack("<10f", first_result) == (0.0,) * 10
    second_samples = struct.unpack("<10f", second_result)
    assert second_samples[0] == 1.0
    assert all(sample == 0.0 for sample in second_samples[1:])


def test_reverb_delay_preserves_state_between_buffers():
    samples = [0.0] * 10 + [0.5] + [0.0] * 9
    effect = AudioReverbDelay()
    effect.configure(1000, 1, delay_ms=10.0, feedback=0.0, mix=1.0)

    first = struct.pack("<10f", *samples[:10])
    second = struct.pack("<10f", *samples[10:])
    result = effect.process(first, "float32", 1) + effect.process(second, "float32", 1)
    output = struct.unpack("<20f", result)

    assert output[10] == 0.0
    assert output[11] == 0.5


def test_reverb_delay_zero_mix_keeps_data():
    data = struct.pack("<3f", 0.1, -0.2, 0.3)
    effect = AudioReverbDelay()
    effect.configure(44100, 1, mix=0.0)
    assert effect.process(data, "float32", 1) == data


def test_reverb_delay_rejects_invalid_configuration():
    effect = AudioReverbDelay()
    invalid = [
        (0, 1, 120.0, 0.35, 0.25),
        (44100, 0, 120.0, 0.35, 0.25),
        (44100, 1, 5.0, 0.35, 0.25),
        (44100, 1, 120.0, 1.0, 0.25),
        (44100, 1, 120.0, 0.35, 1.1),
    ]
    for config in invalid:
        try:
            effect.configure(*config)
        except ValueError:
            pass
        else:
            raise AssertionError("Era esperado ValueError")
