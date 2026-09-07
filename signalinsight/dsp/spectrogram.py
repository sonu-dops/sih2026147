"""Short-Time Fourier Transform (STFT) Spectrogram computation."""

from typing import NamedTuple, Optional
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.constants import DEFAULT_FFT_SIZE, WINDOW_HANN
from signalinsight.io.validator import SignalValidator


class SpectrogramResult(NamedTuple):
    times: np.ndarray        # Time axis in seconds
    frequencies: np.ndarray  # Frequency axis in Hz (centered)
    spectrogram_db: np.ndarray  # 2D matrix: [freq_bins, time_bins] in dBFS
    dynamic_range_db: float
    window_name: str
    nperseg: int


class SpectrogramEngine:
    """Computes Short-Time Fourier Transform for 2D waterfall and spectrogram display."""

    @classmethod
    def compute_spectrogram(
        cls,
        samples: np.ndarray,
        sample_rate: float,
        nperseg: int = 512,
        noverlap: Optional[int] = None,
        window_name: str = WINDOW_HANN,
        center_freq: float = 0.0,
        dynamic_range_db: float = 80.0,
        max_time_bins: int = 1000,
    ) -> SpectrogramResult:
        """
        Computes 2D spectrogram matrix in dBFS.
        Automatically downsamples temporal slices if recording is very long to protect GUI FPS.
        """
        SignalValidator.validate_samples(samples)

        if noverlap is None:
            noverlap = nperseg // 2

        actual_nperseg = min(len(samples), nperseg)
        actual_noverlap = min(actual_nperseg - 1, noverlap)

        w_str = window_name.lower()
        if "hann" in w_str:
            win = "hann"
        elif "hamming" in w_str:
            win = "hamming"
        elif "blackman" in w_str:
            win = "blackman"
        else:
            win = "hann"

        return_onesided = not np.iscomplexobj(samples)

        freqs, times, Zxx = sp_signal.spectrogram(
            samples,
            fs=sample_rate,
            window=win,
            nperseg=actual_nperseg,
            noverlap=actual_noverlap,
            return_onesided=return_onesided,
            mode="psd",
        )

        if np.iscomplexobj(samples):
            # Shift frequencies to center
            freqs = np.fft.fftshift(freqs) + center_freq
            Zxx = np.fft.fftshift(Zxx, axes=0)
        else:
            freqs = freqs + center_freq

        # Safe dB magnitude
        safe_z = np.maximum(Zxx, 1e-18)
        spec_db = 10.0 * np.log10(safe_z)

        # Dynamic range normalization relative to maximum peak
        max_val = np.max(spec_db)
        min_val = max_val - dynamic_range_db
        spec_db_clipped = np.clip(spec_db, min_val, max_val)

        # Decimate time bins if excessive for visualization
        if spec_db_clipped.shape[1] > max_time_bins:
            step = spec_db_clipped.shape[1] // max_time_bins
            spec_db_clipped = spec_db_clipped[:, ::step]
            times = times[::step]

        return SpectrogramResult(
            times=times,
            frequencies=freqs,
            spectrogram_db=spec_db_clipped,
            dynamic_range_db=dynamic_range_db,
            window_name=window_name,
            nperseg=actual_nperseg,
        )
