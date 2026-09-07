"""Constellation metrics, EVM calculation, and decision region analysis."""

from typing import NamedTuple, Tuple
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel


class ConstellationMetrics(NamedTuple):
    evm_rms_pct: ParameterValue
    evm_peak_pct: ParameterValue
    magnitude_error_pct: ParameterValue
    phase_error_deg: ParameterValue
    reference_symbols: np.ndarray


class ConstellationAnalyzer:
    """
    Computes Error Vector Magnitude (EVM), magnitude error, and phase error
    between synchronized received symbols and ideal reference constellation points.
    """

    @classmethod
    def analyze(
        cls,
        received_symbols: np.ndarray,
        ideal_constellation: np.ndarray,
    ) -> ConstellationMetrics:
        if len(received_symbols) == 0 or len(ideal_constellation) == 0:
            nan_val = ParameterValue(name="EVM", value=None, unit="%", quality=QualityLevel.INVALID)
            return ConstellationMetrics(nan_val, nan_val, nan_val, nan_val, np.array([]))

        # Normalize received symbols to average unit energy
        recv_p = np.mean(np.abs(received_symbols) ** 2)
        norm_recv = received_symbols / np.sqrt(max(recv_p, 1e-12))

        # Normalize ideal constellation to unit average power
        ideal_p = np.mean(np.abs(ideal_constellation) ** 2)
        norm_ideal = ideal_constellation / np.sqrt(max(ideal_p, 1e-12))

        # Nearest neighbor association: for each received symbol, find closest ideal symbol
        # Distance matrix: [num_recv, num_ideal]
        diffs = norm_recv[:, None] - norm_ideal[None, :]
        dist_sq = np.abs(diffs) ** 2
        nearest_idx = np.argmin(dist_sq, axis=1)
        ref_symbols = norm_ideal[nearest_idx]

        # Error vector: e_k = r_k - s_k
        error_vector = norm_recv - ref_symbols
        sum_e_sq = float(np.sum(np.abs(error_vector) ** 2))
        sum_ref_sq = float(np.sum(np.abs(ref_symbols) ** 2))

        # EVM RMS = sqrt( sum(|e|^2) / sum(|s|^2) ) * 100%
        evm_rms_pct = float(np.sqrt(sum_e_sq / max(sum_ref_sq, 1e-12)) * 100.0)

        # Peak EVM %
        max_e = float(np.max(np.abs(error_vector)))
        evm_peak_pct = float((max_e / np.sqrt(max(1.0, sum_ref_sq / len(norm_recv)))) * 100.0)

        # Magnitude Error %
        mag_diff = np.abs(norm_recv) - np.abs(ref_symbols)
        mag_err_pct = float(np.sqrt(np.mean(mag_diff ** 2)) * 100.0)

        # Phase Error (degrees)
        phase_diff_rad = (np.angle(norm_recv) - np.angle(ref_symbols) + np.pi) % (2.0 * np.pi) - np.pi
        phase_err_deg = float(np.sqrt(np.mean(phase_diff_rad ** 2)) * (180.0 / np.pi))

        conf = 0.95 if evm_rms_pct < 30.0 else 0.70
        quality = QualityLevel.HIGH if evm_rms_pct < 20.0 else QualityLevel.MEDIUM

        return ConstellationMetrics(
            evm_rms_pct=ParameterValue(
                name="EVM RMS",
                value=evm_rms_pct,
                unit="%",
                source=ProvenanceSource.CALCULATED,
                method="100 * sqrt(sum(|e|^2) / sum(|s|^2))",
                confidence=conf,
                quality=quality,
            ),
            evm_peak_pct=ParameterValue(
                name="EVM Peak",
                value=evm_peak_pct,
                unit="%",
                source=ProvenanceSource.CALCULATED,
                method="Max(|e|) / RMS(|s|)",
                confidence=conf,
                quality=quality,
            ),
            magnitude_error_pct=ParameterValue(
                name="Magnitude Error",
                value=mag_err_pct,
                unit="%",
                source=ProvenanceSource.CALCULATED,
                method="RMS(|r| - |s|) * 100%",
                confidence=conf,
                quality=quality,
            ),
            phase_error_deg=ParameterValue(
                name="Phase Error",
                value=phase_err_deg,
                unit="deg",
                source=ProvenanceSource.CALCULATED,
                method="RMS(angle(r) - angle(s))",
                confidence=conf,
                quality=quality,
            ),
            reference_symbols=ref_symbols,
        )
