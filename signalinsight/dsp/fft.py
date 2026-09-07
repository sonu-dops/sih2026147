"""High-performance windowed FFT and spectral analysis."""

from typing import NamedTuple, Optional, Tuple
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.constants import (
    DEFAULT_FFT_SIZE,
    WINDOW_BLACKMAN,
    WINDOW_FLATTOP,
    WINDOW_HAMMING,
    WINDOW_HANN,
    WINDOW_RECTANGULAR,
)
from signalinsight.core.exceptions import NumericalInstabilityError
from signalinsight.io.validator import SignalValidator


class SpectrumResult(NamedTuple):
    frequencies: np.ndarray  # Centered frequency axis in Hz
    magnitude: np.ndarray    # Linear magnitude |X[k]|
    power: np.ndarray        # Normalized power |X[k]|^2 / N
    power_db: np.ndarray     # Power in dBFS: 10*log10(power)
    peak_frequency: float    # Estimated peak frequency (interpolated)
    peak_power_db: float     # Peak power in dBFS
    window_name: str
    fft_size: int


class FFTEngine:
    """Computes windowed discrete Fourier transforms with consistent scaling conventions."""

    @staticmethod
    def get_window(name: str, length: int) -> np.ndarray:
        """Generates window function by name."""
        name_lower = name.lower()
        if "hann" in name_lower:
            return sp_signal.windows.hann(length, sym=False)
        elif "hamming" in name_lower:
            return sp_signal.windows.hamming(length, sym=False)
        elif "blackman" in name_lower:
            return sp_signal.windows.blackman(length, sym=False)
        elif "flat" in name_lower:
            return sp_signal.windows.flattop(length, sym=False)
        elif "rect" in name_lower:
            return np.ones(length, dtype=np.float64)
        else:
            return sp_signal.windows.hann(length, sym=False)

    @classmethod
    def compute_spectrum(
        cls,
        samples: np.ndarray,
        sample_rate: float,
        fft_size: int = DEFAULT_FFT_SIZE,
        window_name: str = WINDOW_HANN,
        center_freq: float = 0.0,
    ) -> SpectrumResult:
        """
        Computes centered, windowed FFT spectrum.
        Uses coherent amplitude normalization so peak tones reflect true sinusoidal amplitude.
        """
        SignalValidator.validate_samples(samples)
        if len(samples) < fft_size:
            # Zero pad or truncate
            padded = np.zeros(fft_size, dtype=samples.dtype)
            padded[: len(samples)] = samples
            buf = padded
        else:
            buf = samples[:fft_size]

        w = cls.get_window(window_name, fft_size)
        w_sum = np.sum(w)
        if w_sum <= 0:
            w_sum = 1.0

        # Windowed samples
        windowed = buf * w

        # Centered FFT
        X = np.fft.fft(windowed, n=fft_size)
        X_shifted = np.fft.fftshift(X)

        # Centered frequency bins
        # For complex baseband: [-Fs/2, Fs/2) + center_freq
        freqs = np.fft.fftshift(np.fft.fftfreq(fft_size, d=1.0 / sample_rate)) + center_freq

        # Coherent magnitude: |X| / sum(w)
        magnitude = np.abs(X_shifted) / w_sum

        # Power normalized by window energy sum(w^2)
        w_energy = np.sum(w ** 2)
        power = (np.abs(X_shifted) ** 2) / (w_energy if w_energy > 0 else 1.0)

        # Power in dBFS with safe epsilon floor
        safe_power = np.maximum(power, 1e-15)
        power_db = 10.0 * np.log10(safe_power)

        # Peak detection with quadratic sub-bin interpolation
        peak_idx = int(np.argmax(power_db))
        interp_freq, interp_db = cls.interpolate_peak(freqs, power_db, peak_idx)

        return SpectrumResult(
            frequencies=freqs,
            magnitude=magnitude,
            power=power,
            power_db=power_db,
            peak_frequency=interp_freq,
            peak_power_db=interp_db,
            window_name=window_name,
            fft_size=fft_size,
        )

    @staticmethod
    def interpolate_peak(
        freqs: np.ndarray,
        power_db: np.ndarray,
        peak_idx: int,
    ) -> Tuple[float, float]:
        """Quadratic interpolation around spectral peak for high frequency resolution."""
        n = len(freqs)
        if peak_idx <= 0 or peak_idx >= n - 1:
            return float(freqs[peak_idx]), float(power_db[peak_idx])

        alpha = power_db[peak_idx - 1]
        beta = power_db[peak_idx]
        gamma = power_db[peak_idx + 1]

        denom = alpha - 2.0 * beta + gamma
        if abs(denom) < 1e-12:
            return float(freqs[peak_idx]), float(beta)

        # Fractional bin offset in [-0.5, 0.5]
        p = 0.5 * (alpha - gamma) / denom
        df = freqs[1] - freqs[0]
        interpolated_freq = freqs[peak_idx] + p * df
        interpolated_db = beta - 0.25 * (alpha - gamma) * p

        return float(interpolated_freq), float(interpolated_db)
