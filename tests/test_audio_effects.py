from pathlib import Path
import sys
import struct

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.audio_effects import AudioEffects


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
