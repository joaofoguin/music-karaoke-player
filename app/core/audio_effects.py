from __future__ import annotations

import struct


class AudioEffects:
    """Processadores de áudio PCM independentes da camada de reprodução."""

    @staticmethod
    def mix_to_mono(data: bytes, sample_format: str, channel_count: int) -> bytes:
        """Converte PCM intercalado para mono por média dos canais."""
        if channel_count <= 1 or not data:
            return data

        if sample_format == "int16":
            return AudioEffects._mix_int16(data, channel_count)
        if sample_format == "int32":
            return AudioEffects._mix_int32(data, channel_count)
        if sample_format == "float32":
            return AudioEffects._mix_float32(data, channel_count)
        if sample_format == "uint8":
            return AudioEffects._mix_uint8(data, channel_count)

        raise ValueError(f"Formato PCM não suportado: {sample_format}")

    @staticmethod
    def mono_to_channels(data: bytes, sample_format: str, channel_count: int) -> bytes:
        """Duplica um sinal mono para todos os canais de saída."""
        if channel_count <= 1 or not data:
            return data

        if sample_format == "int16":
            samples = struct.unpack(f"<{len(data) // 2}h", data)
            return struct.pack(
                f"<{len(samples) * channel_count}h",
                *(sample for sample in samples for _ in range(channel_count)),
            )
        if sample_format == "int32":
            samples = struct.unpack(f"<{len(data) // 4}i", data)
            return struct.pack(
                f"<{len(samples) * channel_count}i",
                *(sample for sample in samples for _ in range(channel_count)),
            )
        if sample_format == "float32":
            samples = struct.unpack(f"<{len(data) // 4}f", data)
            return struct.pack(
                f"<{len(samples) * channel_count}f",
                *(sample for sample in samples for _ in range(channel_count)),
            )
        if sample_format == "uint8":
            return bytes(
                sample
                for sample in data
                for _ in range(channel_count)
            )

        raise ValueError(f"Formato PCM não suportado: {sample_format}")

    @staticmethod
    def _mix_int16(data: bytes, channel_count: int) -> bytes:
        sample_count = len(data) // 2
        usable_count = sample_count - (sample_count % channel_count)
        samples = struct.unpack(f"<{usable_count}h", data[: usable_count * 2])
        output = []
        for offset in range(0, usable_count, channel_count):
            mixed = round(sum(samples[offset : offset + channel_count]) / channel_count)
            output.append(max(-32768, min(32767, mixed)))
        return struct.pack(f"<{len(output)}h", *output)

    @staticmethod
    def _mix_int32(data: bytes, channel_count: int) -> bytes:
        sample_count = len(data) // 4
        usable_count = sample_count - (sample_count % channel_count)
        samples = struct.unpack(f"<{usable_count}i", data[: usable_count * 4])
        output = []
        for offset in range(0, usable_count, channel_count):
            mixed = round(sum(samples[offset : offset + channel_count]) / channel_count)
            output.append(max(-2147483648, min(2147483647, mixed)))
        return struct.pack(f"<{len(output)}i", *output)

    @staticmethod
    def _mix_float32(data: bytes, channel_count: int) -> bytes:
        sample_count = len(data) // 4
        usable_count = sample_count - (sample_count % channel_count)
        samples = struct.unpack(f"<{usable_count}f", data[: usable_count * 4])
        output = []
        for offset in range(0, usable_count, channel_count):
            mixed = sum(samples[offset : offset + channel_count]) / channel_count
            output.append(max(-1.0, min(1.0, mixed)))
        return struct.pack(f"<{len(output)}f", *output)

    @staticmethod
    def _mix_uint8(data: bytes, channel_count: int) -> bytes:
        usable_count = len(data) - (len(data) % channel_count)
        samples = data[:usable_count]
        output = bytearray()
        for offset in range(0, usable_count, channel_count):
            mixed = round(sum(samples[offset : offset + channel_count]) / channel_count)
            output.append(max(0, min(255, mixed)))
        return bytes(output)


    @staticmethod
    def normalize_peak(
        data: bytes,
        sample_format: str,
        target_peak: float = 0.8912509381,
    ) -> bytes:
        """Normaliza o pico do buffer para o nível-alvo sem ultrapassá-lo."""
        if not data:
            return data

        target_peak = float(target_peak)
        if not 0.0 < target_peak <= 1.0:
            raise ValueError("Pico-alvo inválido")

        if sample_format == "int16":
            samples = struct.unpack(f"<{len(data) // 2}h", data)
            peak = max((abs(sample) for sample in samples), default=0)
            if peak == 0:
                return data
            scale = target_peak * 32767.0 / peak
            return struct.pack(
                f"<{len(samples)}h",
                *(max(-32768, min(32767, round(sample * scale))) for sample in samples),
            )
        if sample_format == "int32":
            samples = struct.unpack(f"<{len(data) // 4}i", data)
            peak = max((abs(sample) for sample in samples), default=0)
            if peak == 0:
                return data
            scale = target_peak * 2147483647.0 / peak
            return struct.pack(
                f"<{len(samples)}i",
                *(max(-2147483648, min(2147483647, round(sample * scale))) for sample in samples),
            )
        if sample_format == "float32":
            samples = struct.unpack(f"<{len(data) // 4}f", data)
            peak = max((abs(sample) for sample in samples), default=0.0)
            if peak == 0:
                return data
            scale = target_peak / peak
            return struct.pack(
                f"<{len(samples)}f",
                *(max(-1.0, min(1.0, sample * scale)) for sample in samples),
            )
        if sample_format == "uint8":
            peak = max((abs(sample - 128) for sample in data), default=0)
            if peak == 0:
                return data
            scale = target_peak * 127.0 / peak
            return bytes(
                max(0, min(255, round(128 + (sample - 128) * scale)))
                for sample in data
            )

        raise ValueError(f"Formato PCM não suportado: {sample_format}")

    @staticmethod
    def apply_gain(data: bytes, sample_format: str, gain_db: float) -> bytes:
        """Aplica ganho linear em decibéis ao PCM, com limitação por formato."""
        if not data or gain_db == 0:
            return data

        import math
        gain = 10 ** (float(gain_db) / 20.0)
        if not math.isfinite(gain):
            raise ValueError("Ganho inválido")

        if sample_format == "int16":
            samples = struct.unpack(f"<{len(data) // 2}h", data)
            processed = [max(-32768, min(32767, round(sample * gain))) for sample in samples]
            return struct.pack(f"<{len(processed)}h", *processed)
        if sample_format == "int32":
            samples = struct.unpack(f"<{len(data) // 4}i", data)
            processed = [max(-2147483648, min(2147483647, round(sample * gain))) for sample in samples]
            return struct.pack(f"<{len(processed)}i", *processed)
        if sample_format == "float32":
            samples = struct.unpack(f"<{len(data) // 4}f", data)
            processed = [max(-1.0, min(1.0, sample * gain)) for sample in samples]
            return struct.pack(f"<{len(processed)}f", *processed)
        if sample_format == "uint8":
            processed = []
            for sample in data:
                value = 128 + (sample - 128) * gain
                processed.append(max(0, min(255, round(value))))
            return bytes(processed)

        raise ValueError(f"Formato PCM não suportado: {sample_format}")
