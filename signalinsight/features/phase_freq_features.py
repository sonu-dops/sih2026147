"""Phase and instantaneous frequency statistical features."""

from typing import Dict
import numpy as np
from scipy import stats

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel
from signalinsight.dsp.analytic import AnalyticSignalEngine


class PhaseFrequencyFeaturesCalculator:
    """Extracts phase transition statistics and instantaneous frequency variation."""

    @classmethod
    def compute(cls, samples: np.ndarray, sample_rate: float) -> Dict[str, ParameterValue]:
        props = AnalyticSignalEngine.compute_properties(samples, sample_rate=sample_rate)

        # Restrict to reliable central region
        mask = props.reliable_mask
        if not np.any(mask):
            mask = np.ones(len(samples), dtype=bool)

        unwrapped = props.unwrapped_phase[mask]
        f_inst = props.instantaneous_frequency[mask]

        # Phase detrending (remove linear carrier frequency ramp)
        residual_phase, slope = AnalyticSignalEngine.detrend_phase(unwrapped)

        phase_var = float(np.var(residual_phase))
        phase_std = float(np.std(residual_phase))

        # Phase transitions: compute modulo-pi or modulo-2pi jumps
        phase_diff = np.abs(np.diff(residual_phase))
        # Large jumps > pi/4 indicate symbol constellation transitions
        phase_jump_count = int(np.sum(phase_diff > (np.pi / 4.0)))
        phase_jump_rate = float(phase_jump_count / max(1, len(phase_diff)))

        # Frequency statistics
        f_mean = float(np.mean(f_inst))
        f_std = float(np.std(f_inst))
        f_var = float(np.var(f_inst))
        f_residual = f_inst - f_mean
        delta_f_mean = float(np.mean(np.abs(f_residual)))
        f_peak_dev = float(np.max(np.abs(f_residual)))

        # Frequency kurtosis: FSK typically shows bimodal/multimodal distribution
        f_kurt = float(stats.kurtosis(f_inst))

        def _p(name: str, val: float, unit: str, method: str) -> ParameterValue:
            return ParameterValue(
                name=name,
                value=val,
                unit=unit,
                source=ProvenanceSource.CALCULATED,
                method=method,
                confidence=0.90,
                quality=QualityLevel.HIGH,
            )

        return {
            "phase_variance": _p("Residual Phase Variance", phase_var, "rad^2", "Var(phi - slope*t)"),
            "phase_std": _p("Residual Phase Std Dev", phase_std, "rad", "Std Dev of residual phase"),
            "phase_jump_rate": _p("Phase Transition Rate", phase_jump_rate, "jumps/sample", "Fraction of jumps > pi/4"),
            "freq_mean": _p("Instantaneous Freq Mean", f_mean, "Hz", "Mean of smoothed dphi/dt"),
            "freq_std": _p("Instantaneous Freq Std Dev", f_std, "Hz", "Std Dev of instantaneous frequency"),
            "freq_mean_deviation": _p("Mean Frequency Deviation", delta_f_mean, "Hz", "Mean(|f_inst - f_c|)"),
            "freq_peak_deviation": _p("Peak Frequency Deviation", f_peak_dev, "Hz", "Max(|f_inst - f_c|)"),
            "freq_kurtosis": _p("Instantaneous Freq Kurtosis", f_kurt, "moment", "Fisher kurtosis of f_inst"),
        }
