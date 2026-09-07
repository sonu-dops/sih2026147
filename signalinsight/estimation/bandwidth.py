"""Occupied Bandwidth (OBW) and -3dB/-6dB bandwidth estimation."""

from typing import NamedTuple
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord
from signalinsight.dsp.psd import PSDEngine, PSDResult
from signalinsight.estimation.base import ParameterEstimator


class BandwidthResult(NamedTuple):
    obw_99_hz: ParameterValue
    obw_95_hz: ParameterValue
    obw_90_hz: ParameterValue
    bandwidth_3db_hz: ParameterValue
    bandwidth_6db_hz: ParameterValue
    f_low_99: float
    f_high_99: float


class BandwidthEstimator(ParameterEstimator):
    """
    Computes Occupied Bandwidth (OBW) via cumulative PSD integration
    and power threshold bandwidths (-3dB, -6dB).
    """

    def estimate(
        self,
        signal_rec: SignalRecord,
        nperseg: int = 2048,
        **kwargs,
    ) -> BandwidthResult:
        psd_res: PSDResult = PSDEngine.compute_psd(
            signal_rec.samples,
            sample_rate=signal_rec.sample_rate,
            nperseg=nperseg,
        )

        freqs = psd_res.frequencies
        psd = psd_res.psd_linear
        psd_db = psd_res.psd_db_hz

        # Cumulative power distribution
        df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
        total_p = np.sum(psd)

        if total_p <= 0:
            nan_val = ParameterValue(name="OBW", value=None, unit="Hz", quality=QualityLevel.INVALID)
            return BandwidthResult(nan_val, nan_val, nan_val, nan_val, nan_val, 0.0, 0.0)

        cum_power = np.cumsum(psd) / total_p

        # 99% OBW: between 0.5% and 99.5%
        f_low_99 = float(np.interp(0.005, cum_power, freqs))
        f_high_99 = float(np.interp(0.995, cum_power, freqs))
        obw_99 = max(0.0, f_high_99 - f_low_99)

        # 95% OBW: between 2.5% and 97.5%
        f_low_95 = float(np.interp(0.025, cum_power, freqs))
        f_high_95 = float(np.interp(0.975, cum_power, freqs))
        obw_95 = max(0.0, f_high_95 - f_low_95)

        # 90% OBW: between 5.0% and 95.0%
        f_low_90 = float(np.interp(0.05, cum_power, freqs))
        f_high_90 = float(np.interp(0.95, cum_power, freqs))
        obw_90 = max(0.0, f_high_90 - f_low_90)

        # -3dB and -6dB bandwidth around maximum peak
        peak_idx = int(np.argmax(psd_db))
        peak_val = psd_db[peak_idx]

        bw_3db = self._calculate_threshold_bw(freqs, psd_db, peak_idx, peak_val - 3.0)
        bw_6db = self._calculate_threshold_bw(freqs, psd_db, peak_idx, peak_val - 6.0)

        val_obw_99 = ParameterValue(
            name="99% Occupied Bandwidth",
            value=float(obw_99),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="PSD Cumulative Energy Integration (99%)",
            confidence=0.92,
            quality=QualityLevel.HIGH if obw_99 > 0 else QualityLevel.LOW,
            notes=f"Band limits: [{f_low_99:+,.1f} Hz to {f_high_99:+,.1f} Hz]",
        )

        val_obw_95 = ParameterValue(
            name="95% Occupied Bandwidth",
            value=float(obw_95),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="PSD Cumulative Energy Integration (95%)",
            confidence=0.92,
            quality=QualityLevel.HIGH if obw_95 > 0 else QualityLevel.LOW,
        )

        val_obw_90 = ParameterValue(
            name="90% Occupied Bandwidth",
            value=float(obw_90),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="PSD Cumulative Energy Integration (90%)",
            confidence=0.92,
            quality=QualityLevel.HIGH if obw_90 > 0 else QualityLevel.LOW,
        )

        val_3db = ParameterValue(
            name="-3 dB Bandwidth",
            value=float(bw_3db),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="Peak PSD -3 dB Contour",
            confidence=0.88,
            quality=QualityLevel.HIGH if bw_3db > 0 else QualityLevel.MEDIUM,
        )

        val_6db = ParameterValue(
            name="-6 dB Bandwidth",
            value=float(bw_6db),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="Peak PSD -6 dB Contour",
            confidence=0.88,
            quality=QualityLevel.HIGH if bw_6db > 0 else QualityLevel.MEDIUM,
        )

        return BandwidthResult(
            obw_99_hz=val_obw_99,
            obw_95_hz=val_obw_95,
            obw_90_hz=val_obw_90,
            bandwidth_3db_hz=val_3db,
            bandwidth_6db_hz=val_6db,
            f_low_99=f_low_99,
            f_high_99=f_high_99,
        )

    @staticmethod
    def _calculate_threshold_bw(
        freqs: np.ndarray,
        psd_db: np.ndarray,
        peak_idx: int,
        threshold_db: float,
    ) -> float:
        """Finds contiguous frequency span around peak above threshold_db."""
        n = len(freqs)
        # Search left
        left_idx = peak_idx
        while left_idx > 0 and psd_db[left_idx] >= threshold_db:
            left_idx -= 1

        # Search right
        right_idx = peak_idx
        while right_idx < n - 1 and psd_db[right_idx] >= threshold_db:
            right_idx += 1

        f_left = freqs[left_idx]
        f_right = freqs[right_idx]
        return float(max(0.0, f_right - f_left))
