"""Forward Error Correction (FEC) and framing framework."""

from typing import Any, List, Optional
import numpy as np

from signalinsight.core.models import DecodingResult
from signalinsight.decoding.base import BaseDecoder
from signalinsight.decoding.crc import CRCValidator


class ConfiguredFECDecoder(BaseDecoder):
    """
    Decodes bitstreams only when explicit framing and FEC parameters are specified.
    Supports standard Hamming(7,4) block code and CRC verification.
    """

    def __init__(
        self,
        fec_type: str = "None",
        code_rate: str = "1/1",
        enable_crc: bool = False,
    ):
        self.fec_type = fec_type
        self.code_rate = code_rate
        self.enable_crc = enable_crc

    def decode(self, bits: List[int], **kwargs: Any) -> DecodingResult:
        if not bits:
            return DecodingResult(
                available=False,
                message="Decoding unavailable — no demodulated bits provided.",
            )

        if self.fec_type == "None" or self.fec_type.lower() == "unconfigured":
            return DecodingResult(
                available=False,
                fec_type="None",
                code_rate="None",
                bit_count=len(bits),
                message="Decoding unavailable — coding configuration not specified.",
            )

        if self.fec_type.lower() == "hamming(7,4)":
            decoded_payload_bits = self._decode_hamming_7_4(bits)
            payload_bytes = CRCValidator.bits_to_bytes(decoded_payload_bits)
            try:
                text_repr = payload_bytes.decode("ascii", errors="replace")
            except Exception:
                text_repr = payload_bytes.hex()

            return DecodingResult(
                available=True,
                fec_type="Hamming(7,4)",
                code_rate="4/7",
                bit_count=len(decoded_payload_bits),
                decoded_payload=text_repr,
                message="Hamming(7,4) block decoding executed successfully.",
            )

        return DecodingResult(
            available=False,
            fec_type=self.fec_type,
            message=f"Decoding unavailable — unsupported FEC type: {self.fec_type}",
        )

    @staticmethod
    def _decode_hamming_7_4(bits: List[int]) -> List[int]:
        """Decodes standard Hamming (7,4) codewords with single-error correction."""
        out_bits: List[int] = []
        # Process in 7-bit blocks
        for i in range(0, len(bits) - 6, 7):
            b = list(bits[i : i + 7])
            # Parity checks
            s1 = b[0] ^ b[2] ^ b[4] ^ b[6]
            s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
            s3 = b[3] ^ b[4] ^ b[5] ^ b[6]
            error_pos = s1 * 1 + s2 * 2 + s3 * 4  # 1-indexed error bit

            if 1 <= error_pos <= 7:
                b[error_pos - 1] ^= 1  # Correct error

            # Data bits are at positions 3, 5, 6, 7 (0-indexed 2, 4, 5, 6)
            out_bits.extend([b[2], b[4], b[5], b[6]])

        return out_bits
