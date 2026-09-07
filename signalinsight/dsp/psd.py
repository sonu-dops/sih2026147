"""Welch Power Spectral Density (PSD) estimation."""

from typing import NamedTuple, Optional
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.constants import DEFAULT_FFT_SIZE, WINDOW_HANN
from signalinsight.io.validator import SignalValidator


class PSDResult(NamedTuple):
    frequencies: np.ndarray  # Centered frequency axis in Hz
    psd_linear: np.ndarray   # Linear PSD in Watts/Hz (relative)
    psd_db_hz: np.ndarray    # PSD in dBFS/Hz: 10*log10(psd_linear)
    total_power: float       # Integrated total power across band
    nperseg: int
    noverlap: int
    window_name: str


class PSDEngine:
    """Computes Welch Power Spectral Density with proper scaling and windowing."""

    @classmethod
    def compute_psd(
        cls,
        samples: np.ndarray,
        sample_rate: float,
        nperseg: int = DEFAULT_FFT_SIZE,
        noverlap: Optional[int] = None,
        window_name: str = WINDOW_HANN,
        center_freq: float = 0.0,
    ) -> PSDResult:
        """
        Computes centered Welch PSD for real or complex signals.
        Returns PSD scaled to dBFS/Hz.
        """
        SignalValidator.validate_samples(samples)

        if noverlap is None:
            noverlap = nperseg // 2

        # Ensure nperseg does not exceed signal length
        actual_nperseg = min(len(samples), nperseg)
        actual_noverlap = min(actual_nperseg - 1, noverlap)

        # Map window name
        w_str = window_name.lower()
        if "hann" in w_str:
            win = "hann"
        elif "hamming" in w_str:
            win = "hamming"
        elif "blackman" in w_str:
            win = "blackman"
        elif "flat" in w_str:
            win = "flattop"
        else:
            win = "hann"

        # Complex baseband spectrum is two-sided and centered
        return_onesided = not np.iscomplexobj(samples)

        freqs, psd = sp_signal.welch(
            samples,
            fs=sample_rate,
            window=win,
            nperseg=actual_nperseg,
            noverlap=actual_noverlap,
            return_onesided=return_onesided,
            scaling="density",
        )

        if np.iscomplexobj(samples):
            # Shift to center negative frequencies
            freqs = np.fft.fftshift(freqs) + center_freq
            psd = np.fft.fftshift(psd)
        else:
            freqs = freqs + center_freq

        # Safe dB conversion
        safe_psd = np.maximum(psd, 1e-18)
        psd_db = 10.0 * np.log10(safe_psd)

        # Trapezoidal integration of PSD over frequency to get total power
        df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
        total_power = float(np.sum(psd) * abs(df))

        return PSDResult(
            frequencies=freqs,
            psd_linear=psd,
            psd_db_hz=psd_db,
            total_power=total_power,
            nperseg=actual_nperseg,
            noverlap=actual_noverlap,
            window_name=window_name,
        )
