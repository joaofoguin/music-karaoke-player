from __future__ import annotations

import math
import struct
from dataclasses import dataclass


@dataclass
class _BiquadState:
    x1: float = 0.0
    x2: float = 0.0
    y1: float = 0.0
    y2: float = 0.0


@dataclass(frozen=True)
class _BiquadCoefficients:
    b0: float
    b1: float
    b2: float
    a1: float
    a2: float


class AudioEqualizer:
    """Equalizador paramétrico de três bandas com estado por canal."""

    BANDS_HZ = (100.0, 1000.0, 10000.0)
    MIN_GAIN_DB = -12.0
    MAX_GAIN_DB = 12.0
    DEFAULT_Q = 1.0

    def __init__(self) -> None:
        self._sample_rate = 0
        self._channel_count = 0
        self._gains_db = (0.0, 0.0, 0.0)
        self._coefficients: tuple[_BiquadCoefficients, ...] = ()
        self._states: list[list[_BiquadState]] = []

    def configure(
        self,
        sample_rate: int,
        channel_count: int,
        bass_db: float = 0.0,
        mid_db: float = 0.0,
        treble_db: float = 0.0,
    ) -> None:
        """Configura as três bandas e reinicia o estado dos filtros."""
        sample_rate = int(sample_rate)
        channel_count = int(channel_count)
        gains = tuple(float(gain) for gain in (bass_db, mid_db, treble_db))

        if sample_rate <= 0:
            raise ValueError("Taxa de amostragem inválida")
        if channel_count <= 0:
            raise ValueError("Quantidade de canais inválida")
        if any(
            not math.isfinite(gain)
            or gain < self.MIN_GAIN_DB
            or gain > self.MAX_GAIN_DB
            for gain in gains
        ):
            raise ValueError("Ganho do equalizador inválido")

        self._sample_rate = sample_rate
        self._channel_count = channel_count
        self._gains_db = gains
        self._coefficients = tuple(
            self._peaking_coefficients(frequency, gain)
            for frequency, gain in zip(self.BANDS_HZ, gains)
        )
        self._states = [
            [_BiquadState() for _ in self._coefficients]
            for _ in range(channel_count)
        ]

    def reset(self) -> None:
        """Limpa o estado interno sem alterar a configuração."""
        self._states = [
            [_BiquadState() for _ in self._coefficients]
            for _ in range(self._channel_count)
        ]

    def process(self, data: bytes, sample_format: str, channel_count: int) -> bytes:
        """Processa PCM intercalado mantendo o estado entre buffers."""
        if not data:
            return data
        if channel_count <= 0:
            raise ValueError("Quantidade de canais inválida")
        if channel_count != self._channel_count:
            raise ValueError("Quantidade de canais diferente da configuração")
        if not self._coefficients or all(gain == 0.0 for gain in self._gains_db):
            return data

        samples = self._unpack(data, sample_format)
        usable_count = len(samples) - (len(samples) % channel_count)
        if usable_count == 0:
            return data

        output = list(samples[:usable_count])
        for index in range(usable_count):
            channel = index % channel_count
            value = float(samples[index])
            for band, coefficients in enumerate(self._coefficients):
                state = self._states[channel][band]
                value = self._process_biquad(value, state, coefficients)
            output[index] = self._clamp(value, sample_format)

        return self._pack(output, sample_format)

    @staticmethod
    def _process_biquad(
        sample: float,
        state: _BiquadState,
        coefficients: _BiquadCoefficients,
    ) -> float:
        output = (
            coefficients.b0 * sample
            + coefficients.b1 * state.x1
            + coefficients.b2 * state.x2
            - coefficients.a1 * state.y1
            - coefficients.a2 * state.y2
        )
        state.x2 = state.x1
        state.x1 = sample
        state.y2 = state.y1
        state.y1 = output
        return output

    def _peaking_coefficients(
        self,
        frequency: float,
        gain_db: float,
    ) -> _BiquadCoefficients:
        a = 10.0 ** (gain_db / 40.0)
        omega = 2.0 * math.pi * frequency / self._sample_rate
        alpha = math.sin(omega) / (2.0 * self.DEFAULT_Q)
        cos_omega = math.cos(omega)

        b0 = 1.0 + alpha * a
        b1 = -2.0 * cos_omega
        b2 = 1.0 - alpha * a
        a0 = 1.0 + alpha / a
        a1 = -2.0 * cos_omega
        a2 = 1.0 - alpha / a

        return _BiquadCoefficients(
            b0 / a0,
            b1 / a0,
            b2 / a0,
            a1 / a0,
            a2 / a0,
        )

    @staticmethod
    def _unpack(data: bytes, sample_format: str) -> tuple[float, ...]:
        if sample_format == "float32":
            return struct.unpack(f"<{len(data) // 4}f", data)
        if sample_format == "int16":
            return tuple(sample / 32767.0 for sample in struct.unpack(f"<{len(data) // 2}h", data))
        if sample_format == "int32":
            return tuple(sample / 2147483647.0 for sample in struct.unpack(f"<{len(data) // 4}i", data))
        if sample_format == "uint8":
            return tuple((sample - 128) / 127.0 for sample in data)
        raise ValueError(f"Formato PCM não suportado: {sample_format}")

    @staticmethod
    def _pack(samples: list[float], sample_format: str) -> bytes:
        if sample_format == "float32":
            return struct.pack(
                f"<{len(samples)}f",
                *[max(-1.0, min(1.0, sample)) for sample in samples],
            )
        if sample_format == "int16":
            return struct.pack(
                f"<{len(samples)}h",
                *[
                    max(-32768, min(32767, round(sample * 32767.0)))
                    for sample in samples
                ],
            )
        if sample_format == "int32":
            return struct.pack(
                f"<{len(samples)}i",
                *[
                    max(-2147483648, min(2147483647, round(sample * 2147483647.0)))
                    for sample in samples
                ],
            )
        if sample_format == "uint8":
            return bytes(
                max(0, min(255, round(128.0 + sample * 127.0)))
                for sample in samples
            )
        raise ValueError(f"Formato PCM não suportado: {sample_format}")

    @staticmethod
    def _clamp(sample: float, sample_format: str) -> float:
        if sample_format == "float32":
            return max(-1.0, min(1.0, sample))
        return max(-1.0, min(1.0, sample))

