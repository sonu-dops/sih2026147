"""Cyclic Redundancy Check (CRC) verification routines."""

from typing import List, Optional


class CRCValidator:
    """Verifies standard CRC polynomials on decoded bitstreams."""

    @staticmethod
    def bits_to_bytes(bits: List[int]) -> bytes:
        """Packs a list of binary bits (0 or 1) into bytes."""
        byte_list = []
        for i in range(0, len(bits) - 7, 8):
            val = 0
            for b in bits[i : i + 8]:
                val = (val << 1) | (1 if b else 0)
            byte_list.append(val)
        return bytes(byte_list)

    @staticmethod
    def compute_crc16_ccitt(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
        """Computes 16-bit CRC-CCITT."""
        crc = init
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ poly) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc

    @classmethod
    def verify_crc16(cls, payload_bits: List[int], expected_crc_bits: List[int]) -> bool:
        payload_bytes = cls.bits_to_bytes(payload_bits)
        crc_calc = cls.compute_crc16_ccitt(payload_bytes)

        # Convert expected bits to int
        expected_val = 0
        for b in expected_crc_bits[:16]:
            expected_val = (expected_val << 1) | (1 if b else 0)

        return crc_calc == expected_val
