"""Symbol rate estimation using non-linear spectral correlation and envelope autocorrelation."""

from typing import List, NamedTuple, Optional
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord
from signalinsight.estimation.base import ParameterEstimator


class SymbolRateResult(NamedTuple):
    symbol_rate_baud: ParameterValue
    candidates: List[float]
    estimation_method: str


class SymbolRateEstimator(ParameterEstimator):
    """
    Estimates digital modulation symbol rate (baud rate).
    Uses non-linear envelope squaring (|x|^2 FFT) and autocorrelation peak analysis.
    """

    def estimate(
        self,
        signal_rec: SignalRecord,
        max_candidates: int = 3,
        **kwargs,
    ) -> SymbolRateResult:
        samples = signal_rec.samples
        fs = signal_rec.sample_rate
        n = min(len(samples), 65536)
        x = samples[:n]

        # 1. Non-linear envelope squaring: y[n] = |x[n]|^2
        y = np.abs(x) ** 2
        # Detrend / remove DC
        y = y - np.mean(y)

        # 2. Spectral analysis of y[n] to find discrete clock lines
        fft_size = int(2 ** np.floor(np.log2(len(y))))
        if fft_size < 256:
            val_nan = ParameterValue(
                name="Symbol Rate",
                value=None,
                unit="Baud",
                source=ProvenanceSource.ESTIMATED,
                quality=QualityLevel.INVALID,
                notes="Signal too short for symbol rate estimation",
            )
            return SymbolRateResult(val_nan, [], "N/A")

        w = sp_signal.windows.hann(fft_size, sym=False)
        Y = np.fft.rfft(y[:fft_size] * w)
        freqs = np.fft.rfftfreq(fft_size, d=1.0 / fs)
        mag_y = np.abs(Y)

        # Ignore DC and extreme low frequencies (< 0.5% Fs) and near-Nyquist (> 45% Fs)
        low_idx = max(2, int(0.005 * fft_size))
        high_idx = min(len(freqs) - 2, int(0.48 * fft_size))

        search_mag = mag_y[low_idx:high_idx]
        search_freqs = freqs[low_idx:high_idx]

        candidates: List[float] = []
        best_rate = 0.0
        confidence = 0.5
        quality = QualityLevel.LOW

        if len(search_mag) > 10:
            # Find spectral peaks
            peaks, properties = sp_signal.find_peaks(
                search_mag,
                prominence=np.median(search_mag) * 2.0,
                distance=max(3, int(fft_size * 0.01)),
            )

            if len(peaks) > 0:
                # Sort peaks by prominence
                prominences = properties.get("prominences", search_mag[peaks])
                sorted_peak_indices = np.argsort(prominences)[::-1]

                for p_idx in sorted_peak_indices[:max_candidates]:
                    cand_freq = float(search_freqs[peaks[p_idx]])
                    candidates.append(cand_freq)

                best_rate = candidates[0]
                peak_prom = prominences[sorted_peak_indices[0]]
                median_noise = np.median(search_mag)
                ratio = peak_prom / (median_noise + 1e-12)

                if ratio > 15.0:
                    confidence = 0.90
                    quality = QualityLevel.HIGH
                elif ratio > 6.0:
                    confidence = 0.75
                    quality = QualityLevel.MEDIUM
                else:
                    confidence = 0.55
                    quality = QualityLevel.LOW

        # 3. Fallback to autocorrelation if no strong spectral line
        if best_rate <= 0 or quality == QualityLevel.LOW:
            autocorr_rate, autocorr_conf = self._autocorr_estimate(x, fs)
            if autocorr_rate > 0 and autocorr_conf > confidence:
                best_rate = autocorr_rate
                confidence = autocorr_conf
                quality = QualityLevel.MEDIUM if confidence > 0.7 else QualityLevel.LOW
                if best_rate not in candidates:
                    candidates.insert(0, best_rate)

        method_name = "Squaring Non-linearity (|x|^2 FFT Clock Line)"

        val_sym = ParameterValue(
            name="Symbol Rate",
            value=float(best_rate) if best_rate > 0 else None,
            unit="Baud",
            source=ProvenanceSource.ESTIMATED,
            method=method_name,
            confidence=confidence if best_rate > 0 else 0.0,
            quality=quality if best_rate > 0 else QualityLevel.INVALID,
            notes=f"Candidates: {[f'{c:,.1f}' for c in candidates[:3]]}",
        )

        return SymbolRateResult(
            symbol_rate_baud=val_sym,
            candidates=candidates[:max_candidates],
            estimation_method=method_name,
        )

    @staticmethod
    def _autocorr_estimate(samples: np.ndarray, fs: float) -> tuple[float, float]:
        """Autocorrelation of instantaneous derivative transitions."""
        diff_mag = np.abs(np.diff(samples))
        n_lags = min(len(diff_mag) // 2, 2048)
        if n_lags < 64:
            return 0.0, 0.0

        r = np.correlate(diff_mag[:n_lags * 2] - np.mean(diff_mag), diff_mag[:n_lags * 2] - np.mean(diff_mag), mode="full")
        mid = len(r) // 2
        r_half = r[mid: mid + n_lags]

        # Ignore lag 0 and find first significant peak
        peaks, _ = sp_signal.find_peaks(r_half[2:], distance=3)
        if len(peaks) > 0:
            first_peak_lag = peaks[0] + 2
            if first_peak_lag > 0:
                est_rate = fs / float(first_peak_lag)
                return est_rate, 0.65
        return 0.0, 0.0
