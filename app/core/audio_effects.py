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
