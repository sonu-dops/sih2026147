"""Time domain and amplitude envelope statistical features."""

from typing import Dict
import numpy as np
from scipy import stats

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel


class TimeFeaturesCalculator:
    """Extracts statistical moments and distribution features from time domain & envelope."""

    @staticmethod
    def compute(samples: np.ndarray) -> Dict[str, ParameterValue]:
        env = np.abs(samples)
        env_mean = float(np.mean(env))
        env_std = float(np.std(env))
        env_var = float(np.var(env))
        env_max = float(np.max(env))
        env_min = float(np.min(env))

        # Peak to average ratio of envelope
        par = float(env_max / (env_mean + 1e-12))

        # Higher moments of envelope
        env_skew = float(stats.skew(env))
        env_kurt = float(stats.kurtosis(env))  # Fisher's kurtosis (normal = 0.0)

        # Zero-crossing rate of I component
        i_comp = samples.real
        zero_crossings_i = int(np.sum(np.diff(np.signbit(i_comp))))
        zcr_i = float(zero_crossings_i / max(1, len(samples) - 1))

        # Variance of normalized envelope: gamma_max / envelope variance
        # In BPSK/QAM envelope fluctuates; in continuous FSK envelope is near constant
        norm_env = env / (env_mean + 1e-12)
        norm_env_var = float(np.var(norm_env))

        def _p(name: str, val: float, unit: str, method: str) -> ParameterValue:
            return ParameterValue(
                name=name,
                value=val,
                unit=unit,
                source=ProvenanceSource.CALCULATED,
                method=method,
                confidence=1.0,
                quality=QualityLevel.HIGH,
            )

        return {
            "envelope_mean": _p("Envelope Mean", env_mean, "V", "Mean of |x[n]|"),
            "envelope_std": _p("Envelope Std Dev", env_std, "V", "Std Dev of |x[n]|"),
            "envelope_var": _p("Envelope Variance", env_var, "V^2", "Variance of |x[n]|"),
            "envelope_par": _p("Envelope Peak-to-Average", par, "ratio", "max(|x|) / mean(|x|)"),
            "envelope_skewness": _p("Envelope Skewness", env_skew, "moment", "Fisher skewness of |x|"),
            "envelope_kurtosis": _p("Envelope Kurtosis", env_kurt, "moment", "Excess kurtosis of |x|"),
            "norm_envelope_var": _p("Normalized Envelope Variance", norm_env_var, "ratio", "Var(|x|/mean(|x|))"),
            "zero_crossing_rate_i": _p("I Zero-Crossing Rate", zcr_i, "crossings/sample", "Sign transitions of I"),
        }
