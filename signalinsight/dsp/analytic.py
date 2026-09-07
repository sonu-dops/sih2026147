"""Analytic signal representation, Hilbert transform, and instantaneous properties."""

from typing import NamedTuple, Optional, Tuple
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.exceptions import NumericalInstabilityError
from signalinsight.io.validator import SignalValidator


class InstantaneousSignalProperties(NamedTuple):
    analytic_signal: np.ndarray
    envelope: np.ndarray
    raw_phase: np.ndarray
    unwrapped_phase: np.ndarray
    instantaneous_frequency: np.ndarray
    reliable_mask: np.ndarray  # True for valid central region, False for Hilbert edge transients


class AnalyticSignalEngine:
    """Computes analytic signal and instantaneous amplitude, phase, and frequency."""

    @staticmethod
    def to_analytic(samples: np.ndarray) -> np.ndarray:
        """
        Converts real-valued samples to complex analytic signal via Hilbert transform.
        If already complex, returns samples directly.
        """
        SignalValidator.validate_samples(samples)
        if np.iscomplexobj(samples):
            return samples
        # Real signal -> analytic signal using SciPy Hilbert
        return sp_signal.hilbert(samples.astype(np.float64))

    @classmethod
    def compute_properties(
        cls,
        samples: np.ndarray,
        sample_rate: float,
        smooth_window: int = 15,
        poly_order: int = 3,
        edge_margin_ratio: float = 0.05,
    ) -> InstantaneousSignalProperties:
        """
        Extracts instantaneous envelope, unwrapped phase, and smoothed instantaneous frequency.
        Flags edge boundary regions affected by Hilbert transform Gibbs phenomena.
        """
        z = cls.to_analytic(samples)
        n = len(z)

        # Instantaneous amplitude (envelope)
        envelope = np.abs(z)

        # Instantaneous phase (raw in [-pi, pi])
        raw_phase = np.angle(z)

        # Unwrapped phase
        unwrapped_phase = np.unwrap(raw_phase)

        # Instantaneous frequency: d(phi)/dt / (2*pi)
        # Using central differences and Savitzky-Golay smoothing for numerical robustness
        d_phi = np.gradient(unwrapped_phase)
        raw_f_inst = (sample_rate / (2.0 * np.pi)) * d_phi

        # Smooth instantaneous frequency to reject noise spikes
        if n >= smooth_window and smooth_window > poly_order:
            # Ensure window length is odd
            w_len = smooth_window if smooth_window % 2 == 1 else smooth_window + 1
            if w_len <= n:
                f_inst = sp_signal.savgol_filter(raw_f_inst, window_length=w_len, polyorder=poly_order)
            else:
                f_inst = raw_f_inst
        else:
            f_inst = raw_f_inst

        # Edge boundary mask (True = reliable, False = edge transient)
        edge_samples = int(n * edge_margin_ratio)
        reliable_mask = np.ones(n, dtype=bool)
        if edge_samples > 0:
            reliable_mask[:edge_samples] = False
            reliable_mask[-edge_samples:] = False

        return InstantaneousSignalProperties(
            analytic_signal=z,
            envelope=envelope,
            raw_phase=raw_phase,
            unwrapped_phase=unwrapped_phase,
            instantaneous_frequency=f_inst,
            reliable_mask=reliable_mask,
        )

    @staticmethod
    def detrend_phase(unwrapped_phase: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Removes linear carrier phase ramp.
        Returns (residual_phase, estimated_slope_rad_per_sample).
        """
        n = len(unwrapped_phase)
        x = np.arange(n)
        # Linear fit: phase = slope * n + intercept
        slope, intercept = np.polyfit(x, unwrapped_phase, 1)
        residual = unwrapped_phase - (slope * x + intercept)
        return residual, float(slope)
