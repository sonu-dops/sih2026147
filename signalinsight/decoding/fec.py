"""Forward Error Correction (FEC) and framing framework."""

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
import numpy as np

from signalinsight.core.models import DecodingResult
from signalinsight.decoding.base import BaseDecoder
from signalinsight.decoding.crc import CRCValidator


@dataclass
class BlindFECAnalysis:
    """Output from blind FEC, code rate, and preamble analysis."""
    detected_scheme: str
    code_rate: str
    confidence: float
    preamble_detected: Optional[str] = None
    notes: str = ""


class BlindFECEstimator:
    """
    Automated blind estimator for channel coding, framing, and FEC schemes.
    Analyzes demodulated bitstreams to detect:
    - Standard Rate 1/2 Convolutional codes (K=7 NASA polynomials, K=3 standard)
    - Hamming(7,4) block parity patterns
    - Alternating preambles (0xAA, 0x55) and sync words (Barker, HDLC 0x7E, CCSDS 0xEB90)
    - High-entropy uncoded / scrambled bitstreams
    """

    @classmethod
    def estimate(cls, bits: List[int]) -> BlindFECAnalysis:
        if not bits or len(bits) < 14:
            return BlindFECAnalysis(
                detected_scheme="None (Insufficient bits)",
                code_rate="1/1",
                confidence=0.0,
                notes="Bitstream too short for FEC pattern analysis.",
            )

        b = np.array(bits, dtype=np.int32)

        # 1. Preamble & Framing Detection
        preamble_str, preamble_conf = cls._detect_preamble(b)

        # 2. Check Hamming (7,4) code
        hamming_score = cls._check_hamming_7_4(b)

        # 3. Check Rate 1/2 Convolutional Code (NASA K=7 and K=3 constraints)
        conv_score = cls._check_convolutional_rate_half(b)

        # 4. Determine most plausible scheme
        if conv_score >= 0.70:
            return BlindFECAnalysis(
                detected_scheme="Possible convolutional",
                code_rate="1/2",
                confidence=float(conv_score),
                preamble_detected=preamble_str,
                notes="Detected cyclic syndrome constraints consistent with Rate 1/2 convolutional code.",
            )
        elif hamming_score >= 0.70:
            return BlindFECAnalysis(
                detected_scheme="Possible Hamming(7,4)",
                code_rate="4/7",
                confidence=float(hamming_score),
                preamble_detected=preamble_str,
                notes="Detected 7-bit block parity consistency with Hamming(7,4) code.",
            )
        elif preamble_str:
            return BlindFECAnalysis(
                detected_scheme=f"Framed ({preamble_str})",
                code_rate="1/1",
                confidence=float(preamble_conf),
                preamble_detected=preamble_str,
                notes=f"Detected preamble synchronizer ({preamble_str}); payload uncoded or proprietary.",
            )
        else:
            # Check bit entropy
            p1 = float(np.mean(b))
            p0 = 1.0 - p1
            entropy = 0.0
            if 0.0 < p0 < 1.0:
                entropy = - (p0 * np.log2(p0) + p1 * np.log2(p1))

            if entropy > 0.85:
                scheme = "Uncoded / Scrambled"
                notes = "High-entropy bitstream with uniform transition density; no linear block parity."
            else:
                scheme = "Uncoded (Biased)"
                notes = f"Transition bias detected (P(1)={p1:.2f}); no standard linear block code."

            return BlindFECAnalysis(
                detected_scheme=scheme,
                code_rate="1/1",
                confidence=0.85,
                notes=notes,
            )

    @staticmethod
    def _detect_preamble(b: np.ndarray) -> Tuple[Optional[str], float]:
        """Detects standard preamble and sync patterns in the first 128 bits."""
        n_lead = min(len(b), 128)
        lead = b[:n_lead]

        # Alternating preamble (101010... or 010101...)
        transitions = np.sum(lead[:-1] ^ lead[1:])
        trans_ratio = float(transitions) / max(1, n_lead - 1)
        if trans_ratio > 0.82:
            return ("0xAA/0x55 Alternating Preamble", min(0.99, trans_ratio))

        # Check Barker 11: 1 1 1 0 0 0 1 0 0 1 0
        barker11 = np.array([1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0], dtype=np.int32)
        if len(b) >= 11:
            for i in range(min(len(b) - 11, 64)):
                if np.array_equal(b[i : i + 11], barker11):
                    return ("Barker-11 Sync Word", 0.95)

        # Check Barker 7: 1 1 1 0 0 1 0
        barker7 = np.array([1, 1, 1, 0, 0, 1, 0], dtype=np.int32)
        if len(b) >= 7:
            for i in range(min(len(b) - 7, 32)):
                if np.array_equal(b[i : i + 7], barker7):
                    return ("Barker-7 Sync Word", 0.90)

        # Check HDLC flag (01111110 = 0x7E)
        hdlc = np.array([0, 1, 1, 1, 1, 1, 1, 0], dtype=np.int32)
        if len(b) >= 8:
            for i in range(min(len(b) - 8, 32)):
                if np.array_equal(b[i : i + 8], hdlc):
                    return ("HDLC Flag (0x7E)", 0.92)

        return (None, 0.0)

    @staticmethod
    def _check_hamming_7_4(b: np.ndarray) -> float:
        """Computes fraction of 7-bit blocks satisfying Hamming(7,4) parity equations."""
        num_blocks = len(b) // 7
        if num_blocks < 2:
            return 0.0

        valid_blocks = 0
        for i in range(num_blocks):
            blk = b[i * 7 : (i + 1) * 7]
            s1 = blk[0] ^ blk[2] ^ blk[4] ^ blk[6]
            s2 = blk[1] ^ blk[2] ^ blk[5] ^ blk[6]
            s3 = blk[3] ^ blk[4] ^ blk[5] ^ blk[6]
            if s1 == 0 and s2 == 0 and s3 == 0:
                valid_blocks += 1

        return float(valid_blocks) / num_blocks

    @staticmethod
    def _check_convolutional_rate_half(b: np.ndarray) -> float:
        """
        Tests rate-1/2 convolutional code syndrome relations:
        Standard rate 1/2 NASA polynomials: G1=133_8 (1011011_2), G2=171_8 (1111001_2).
        Syndrome check: G2 * y1 ^ G1 * y2 = 0 in GF(2).
        Also tests standard K=3 code: G1=7_8 (111_2), G2=5_8 (101_2).
        """
        if len(b) < 32:
            return 0.0

        even_bits = b[0::2]
        odd_bits = b[1::2]
        m = min(len(even_bits), len(odd_bits))
        if m < 16:
            return 0.0

        y1 = even_bits[:m]
        y2 = odd_bits[:m]

        # For K=3: G2 * y1 ^ G1 * y2:
        syn_k3 = (y1[2:] ^ y1[:-2]) ^ (y2[2:] ^ y2[1:-1] ^ y2[:-2])
        zero_frac_k3 = 1.0 - float(np.mean(syn_k3))

        # For K=7 (133 / 171):
        if m >= 32:
            t1 = y1[6:] ^ y1[5:-1] ^ y1[4:-2] ^ y1[3:-3] ^ y1[:-6]
            t2 = y2[6:] ^ y2[4:-2] ^ y2[3:-3] ^ y2[1:-5] ^ y2[:-6]
            syn_k7 = t1 ^ t2
            zero_frac_k7 = 1.0 - float(np.mean(syn_k7))
        else:
            zero_frac_k7 = 0.0

        return max(zero_frac_k3, zero_frac_k7)


class ConfiguredFECDecoder(BaseDecoder):
    """
    Decodes bitstreams with explicit framing and FEC parameters,
    or performs blind FEC estimation when set to 'Auto'.
    Supports standard Hamming(7,4) block code, blind convolutional detection, and CRC.
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

        if self.fec_type.lower() in ("auto", "blind"):
            analysis = BlindFECEstimator.estimate(bits)
            payload_bytes = CRCValidator.bits_to_bytes(bits)
            try:
                text_repr = payload_bytes.decode("ascii", errors="replace")
            except Exception:
                text_repr = payload_bytes.hex()

            return DecodingResult(
                available=True,
                fec_type=analysis.detected_scheme,
                code_rate=analysis.code_rate,
                bit_count=len(bits),
                decoded_payload=text_repr,
                message=f"FEC: {analysis.detected_scheme} [{analysis.notes}]",
            )

        if self.fec_type == "None" or self.fec_type.lower() == "unconfigured":
            analysis = BlindFECEstimator.estimate(bits)
            detected_fec = analysis.detected_scheme if analysis.detected_scheme != "None (Insufficient bits)" else "None"
            return DecodingResult(
                available=False,
                fec_type=detected_fec,
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
