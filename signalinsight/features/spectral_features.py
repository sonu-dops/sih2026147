"""Spectral shape features: centroid, spread, skewness, kurtosis, and flatness."""

from typing import Dict
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel
from signalinsight.dsp.psd import PSDEngine


class SpectralFeaturesCalculator:
    """Extracts spectral distribution moments and spectral flatness from PSD."""

    @classmethod
    def compute(cls, samples: np.ndarray, sample_rate: float) -> Dict[str, ParameterValue]:
        psd_res = PSDEngine.compute_psd(samples, sample_rate=sample_rate, nperseg=1024)
        freqs = psd_res.frequencies
        psd = np.maximum(psd_res.psd_linear, 1e-18)

        total_p = np.sum(psd)
        if total_p <= 0:
            total_p = 1e-12

        # 1. Spectral Centroid
        centroid = float(np.sum(freqs * psd) / total_p)

        # 2. Spectral Spread (Standard Deviation)
        spread = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * psd) / total_p))

        # 3. Spectral Skewness
        denom_spread = max(spread, 1e-6)
        skewness = float(np.sum(((freqs - centroid) ** 3) * psd) / ((denom_spread ** 3) * total_p))

        # 4. Spectral Kurtosis
        kurtosis = float(np.sum(((freqs - centroid) ** 4) * psd) / ((denom_spread ** 4) * total_p)) - 3.0

        # 5. Spectral Flatness (Wiener entropy: Geometric Mean / Arithmetic Mean)
        log_psd = np.log(psd)
        geom_mean = np.exp(np.mean(log_psd))
        arith_mean = np.mean(psd)
        flatness = float(geom_mean / (arith_mean + 1e-18))

        def _p(name: str, val: float, unit: str, method: str) -> ParameterValue:
            return ParameterValue(
                name=name,
                value=val,
                unit=unit,
                source=ProvenanceSource.CALCULATED,
                method=method,
                confidence=0.95,
                quality=QualityLevel.HIGH,
            )

        return {
            "spectral_centroid": _p("Spectral Centroid", centroid, "Hz", "Sum(f * P) / Sum(P)"),
            "spectral_spread": _p("Spectral Spread", spread, "Hz", "sqrt(Sum((f - c)^2 * P) / Sum(P))"),
            "spectral_skewness": _p("Spectral Skewness", skewness, "moment", "3rd spectral central moment"),
            "spectral_kurtosis": _p("Spectral Kurtosis", kurtosis, "moment", "4th spectral central moment - 3"),
            "spectral_flatness": _p("Spectral Flatness", flatness, "ratio", "Geometric Mean / Arithmetic Mean"),
        }
