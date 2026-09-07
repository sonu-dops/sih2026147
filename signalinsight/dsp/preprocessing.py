"""Signal preprocessing: DC offset removal, normalization, and detrending."""

import time
from enum import Enum
from typing import NamedTuple, Tuple
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.exceptions import NumericalInstabilityError
from signalinsight.core.models import SignalRecord
from signalinsight.io.validator import SignalValidator


class NormalizationMode(str, Enum):
    PRESERVE = "Preserve Absolute"
    RMS = "Normalize to RMS = 1"
    PEAK = "Normalize to Peak = 1"


class DCOffsetResult(NamedTuple):
    offset_i: float
    offset_q: float
    offset_mag: float
    corrected_samples: np.ndarray


class SignalPreprocessor:
    """Preprocesses raw signals deterministically without mutating inputs."""

    @staticmethod
    def estimate_dc_offset(samples: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate I, Q, and complex magnitude DC offset.
        For real signals, Q is 0.0.
        """
        SignalValidator.validate_samples(samples)
        if np.iscomplexobj(samples):
            i_mean = float(np.mean(samples.real))
            q_mean = float(np.mean(samples.imag))
            mag = float(np.hypot(i_mean, q_mean))
            return i_mean, q_mean, mag
        else:
            mean_val = float(np.mean(samples))
            return mean_val, 0.0, abs(mean_val)

    @classmethod
    def remove_dc_offset(cls, signal_rec: SignalRecord) -> Tuple[SignalRecord, DCOffsetResult]:
        """
        Removes DC bias from complex or real signal.
        Returns a new SignalRecord and the measured DC offset values.
        """
        t0 = time.perf_counter()
        samples = signal_rec.samples
        i_off, q_off, mag_off = cls.estimate_dc_offset(samples)

        if signal_rec.is_complex:
            dc_vector = i_off + 1j * q_off
            corrected = samples - dc_vector
        else:
            corrected = samples - i_off

        elapsed = (time.perf_counter() - t0) * 1000.0

        new_rec = signal_rec.copy()
        new_rec.samples = corrected
        new_rec.add_history(
            stage="DC Offset Removal",
            params={"offset_i": i_off, "offset_q": q_off, "offset_mag": mag_off},
            elapsed_ms=elapsed,
            notes=f"Removed DC offset: I={i_off:.6e}, Q={q_off:.6e}, Mag={mag_off:.6e}",
        )

        dc_res = DCOffsetResult(
            offset_i=i_off,
            offset_q=q_off,
            offset_mag=mag_off,
            corrected_samples=corrected,
        )
        return new_rec, dc_res

    @staticmethod
    def calculate_rms(samples: np.ndarray) -> float:
        """Calculate Root Mean Square (RMS) of complex or real samples."""
        SignalValidator.validate_samples(samples)
        if len(samples) == 0:
            return 0.0
        # Power = mean(|x|^2)
        power = np.mean(np.abs(samples) ** 2)
        return float(np.sqrt(power))

    @classmethod
    def normalize(
        cls,
        signal_rec: SignalRecord,
        mode: NormalizationMode = NormalizationMode.RMS,
    ) -> SignalRecord:
        """Applies RMS or Peak normalization while preserving phase information."""
        if mode == NormalizationMode.PRESERVE:
            return signal_rec.copy()

        t0 = time.perf_counter()
        samples = signal_rec.samples
        SignalValidator.validate_samples(samples)

        if mode == NormalizationMode.RMS:
            rms_val = cls.calculate_rms(samples)
            if rms_val < 1e-12:
                raise NumericalInstabilityError(
                    "Cannot normalize signal: RMS amplitude is near zero (silent signal).",
                    suggested_action="Verify signal presence and input gain.",
                )
            normalized = samples / rms_val
            factor = 1.0 / rms_val
        elif mode == NormalizationMode.PEAK:
            peak_val = float(np.max(np.abs(samples)))
            if peak_val < 1e-12:
                raise NumericalInstabilityError(
                    "Cannot normalize signal: Peak amplitude is near zero.",
                    suggested_action="Verify signal presence.",
                )
            normalized = samples / peak_val
            factor = 1.0 / peak_val
        else:
            raise ValueError(f"Unknown normalization mode: {mode}")

        elapsed = (time.perf_counter() - t0) * 1000.0
        new_rec = signal_rec.copy()
        new_rec.samples = normalized
        new_rec.add_history(
            stage="Normalization",
            params={"mode": mode.value, "scale_factor": float(factor)},
            elapsed_ms=elapsed,
        )
        return new_rec

    @staticmethod
    def detrend(samples: np.ndarray, type_str: str = "linear") -> np.ndarray:
        """Detrends real or complex signal components."""
        if np.iscomplexobj(samples):
            real_dt = sp_signal.detrend(samples.real, type=type_str)
            imag_dt = sp_signal.detrend(samples.imag, type=type_str)
            return real_dt + 1j * imag_dt
        return sp_signal.detrend(samples, type=type_str)
