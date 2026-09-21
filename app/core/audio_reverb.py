from __future__ import annotations

import struct


class AudioReverbDelay:
    """Efeito de atraso com realimentação para ambiência e reverberação leve."""

    MIN_DELAY_MS = 10.0
    MAX_DELAY_MS = 2000.0
    MAX_FEEDBACK = 0.95

    def __init__(self):
        self._sample_rate = 0
        self._channels = 0
        self._delay_samples = 0
        self._feedback = 0.0
        self._mix = 0.0
        self._buffer: list[float] = []
        self._write_index = 0

    def configure(
        self,
        sample_rate: int,
        channel_count: int,
        delay_ms: float = 120.0,
        feedback: float = 0.35,
        mix: float = 0.25,
    ) -> None:
        sample_rate = int(sample_rate)
        channel_count = int(channel_count)
        delay_ms = float(delay_ms)
        feedback = float(feedback)
        mix = float(mix)

        if sample_rate <= 0:
            raise ValueError("Taxa de amostragem inválida")
        if channel_count <= 0:
            raise ValueError("Quantidade de canais inválida")
        if not self.MIN_DELAY_MS <= delay_ms <= self.MAX_DELAY_MS:
            raise ValueError("Tempo de delay inválido")
        if not 0.0 <= feedback <= self.MAX_FEEDBACK:
            raise ValueError("Feedback inválido")
        if not 0.0 <= mix <= 1.0:
            raise ValueError("Mix inválido")

        delay_samples = max(1, round(sample_rate * delay_ms / 1000.0))
        if (
            sample_rate == self._sample_rate
            and channel_count == self._channels
            and delay_samples == self._delay_samples
        ):
            self._feedback = feedback
            self._mix = mix
            return

        self._sample_rate = sample_rate
        self._channels = channel_count
        self._delay_samples = delay_samples
        self._feedback = feedback
        self._mix = mix
        self._buffer = [0.0] * (delay_samples * channel_count)
        self._write_index = 0

    def reset(self) -> None:
        self._buffer = [0.0] * len(self._buffer)
        self._write_index = 0

    def process(self, data: bytes, sample_format: str, channel_count: int) -> bytes:
        if not data or self._mix == 0.0:
            return data

        if channel_count != self._channels or self._delay_samples <= 0:
            raise ValueError("Configuração do reverb/delay incompatível com o PCM")

        if sample_format == "float32":
            samples = list(struct.unpack(f"<{len(data) // 4}f", data))
            processed = self._process_samples(samples)
            return struct.pack(f"<{len(processed)}f", *processed)

        if sample_format == "int16":
            samples = struct.unpack(f"<{len(data) // 2}h", data)
            processed = self._process_samples([sample / 32767.0 for sample in samples])
            return struct.pack(
                f"<{len(processed)}h",
                *(max(-32768, min(32767, round(sample * 32767.0))) for sample in processed),
            )

        if sample_format == "int32":
            samples = struct.unpack(f"<{len(data) // 4}i", data)
            processed = self._process_samples([sample / 2147483647.0 for sample in samples])
            return struct.pack(
                f"<{len(processed)}i",
                *(max(-2147483648, min(2147483647, round(sample * 2147483647.0))) for sample in processed),
            )

        if sample_format == "uint8":
            samples = [(sample - 128) / 127.0 for sample in data]
            processed = self._process_samples(samples)
            return bytes(
                max(0, min(255, round(128 + sample * 127.0)))
                for sample in processed
            )

        raise ValueError(f"Formato PCM não suportado: {sample_format}")

    def _process_samples(self, samples: list[float]) -> list[float]:
        output = []

        for offset, sample in enumerate(samples):
            channel = offset % self._channels
            index = self._write_index + channel
            delayed = self._buffer[index]

            wet = sample + delayed * self._feedback
            mixed = sample * (1.0 - self._mix) + delayed * self._mix
            output.append(max(-1.0, min(1.0, mixed)))

            self._buffer[index] = max(-1.0, min(1.0, wet))
            if channel == self._channels - 1:
                self._write_index += self._channels
                if self._write_index >= len(self._buffer):
                    self._write_index = 0

        return output
