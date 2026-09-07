"""Digital filters and pulse shaping matched filters."""

from enum import Enum
from typing import Optional, Tuple
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.exceptions import NumericalInstabilityError
from signalinsight.core.models import SignalRecord


class PulseShape(str, Enum):
    RECTANGULAR = "Rectangular"
    ROOT_RAISED_COSINE = "Root Raised Cosine"
    RAISED_COSINE = "Raised Cosine"
    GAUSSIAN = "Gaussian"


class FilterEngine:
    """Designs and executes FIR, IIR, and pulse shaping matched filters."""

    @staticmethod
    def design_lowpass_fir(
        sample_rate: float,
        cutoff_hz: float,
        num_taps: int = 101,
        window: str = "hamming",
    ) -> np.ndarray:
        """Designs a linear-phase lowpass FIR filter."""
        nyquist = sample_rate / 2.0
        if cutoff_hz >= nyquist:
            raise ValueError(f"Cutoff frequency ({cutoff_hz} Hz) must be less than Nyquist ({nyquist} Hz)")
        norm_cutoff = cutoff_hz / nyquist
        taps = sp_signal.firwin(num_taps, norm_cutoff, window=window)
        return taps.astype(np.float64)

    @staticmethod
    def design_bandpass_fir(
        sample_rate: float,
        low_cutoff_hz: float,
        high_cutoff_hz: float,
        num_taps: int = 101,
        window: str = "hamming",
    ) -> np.ndarray:
        """Designs a linear-phase bandpass FIR filter."""
        nyquist = sample_rate / 2.0
        if low_cutoff_hz <= 0 or high_cutoff_hz >= nyquist or low_cutoff_hz >= high_cutoff_hz:
            raise ValueError(f"Invalid bandpass cutoffs: [{low_cutoff_hz}, {high_cutoff_hz}] for Fs={sample_rate}")
        norm_pass = [low_cutoff_hz / nyquist, high_cutoff_hz / nyquist]
        taps = sp_signal.firwin(num_taps, norm_pass, pass_zero=False, window=window)
        return taps.astype(np.float64)

    @staticmethod
    def design_rrc_filter(
        samples_per_symbol: int,
        beta: float = 0.35,
        span_symbols: int = 8,
    ) -> np.ndarray:
        """
        Designs a Root-Raised Cosine (RRC) pulse shaping filter.
        Mathematically exact continuous formula evaluated at discrete time points.
        """
        if beta < 0.0 or beta > 1.0:
            raise ValueError(f"RRC roll-off beta must be in [0, 1], got {beta}")
        if samples_per_symbol < 1:
            raise ValueError("samples_per_symbol must be at least 1")

        n_taps = span_symbols * samples_per_symbol + 1
        t = np.arange(-span_symbols / 2.0, span_symbols / 2.0 + 1e-9, 1.0 / samples_per_symbol)
        h = np.zeros_like(t, dtype=np.float64)

        for i, val in enumerate(t):
            if np.isclose(val, 0.0, atol=1e-8):
                h[i] = 1.0 - beta + (4.0 * beta / np.pi)
            elif beta > 0.0 and np.isclose(np.abs(val), 1.0 / (4.0 * beta), atol=1e-8):
                term1 = (1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * beta))
                term2 = (1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * beta))
                h[i] = (beta / np.sqrt(2.0)) * (term1 + term2)
            else:
                numerator = np.sin(np.pi * val * (1.0 - beta)) + 4.0 * beta * val * np.cos(np.pi * val * (1.0 + beta))
                denominator = np.pi * val * (1.0 - (4.0 * beta * val) ** 2)
                h[i] = numerator / denominator

        # Energy normalization so unit energy: sum(h^2) = 1
        energy = np.sum(h ** 2)
        if energy > 0:
            h /= np.sqrt(energy)
        return h

    @classmethod
    def apply_filter(cls, samples: np.ndarray, taps: np.ndarray) -> np.ndarray:
        """Applies FIR filter with correct linear convolution and group delay compensation."""
        if len(samples) < len(taps):
            raise NumericalInstabilityError("Sample length is shorter than filter taps.")

        if np.iscomplexobj(samples):
            i_filt = sp_signal.fftconvolve(samples.real, taps, mode="same")
            q_filt = sp_signal.fftconvolve(samples.imag, taps, mode="same")
            return i_filt + 1j * q_filt
        return sp_signal.fftconvolve(samples, taps, mode="same")

    @classmethod
    def apply_matched_filter(
        cls,
        signal_rec: SignalRecord,
        pulse_shape: PulseShape = PulseShape.ROOT_RAISED_COSINE,
        samples_per_symbol: int = 4,
        beta: float = 0.35,
        span_symbols: int = 8,
    ) -> SignalRecord:
        """
        Applies matched filtering using the time-reversed complex conjugate
        of the specified pulse shape.
        """
        if pulse_shape == PulseShape.ROOT_RAISED_COSINE:
            h = cls.design_rrc_filter(samples_per_symbol, beta=beta, span_symbols=span_symbols)
        else:
            # Simple rectangular boxcar
            h = np.ones(samples_per_symbol, dtype=np.float64) / np.sqrt(samples_per_symbol)

        # Time-reversed conjugate
        matched_taps = np.conj(h[::-1])
        filtered_samples = cls.apply_filter(signal_rec.samples, matched_taps)

        new_rec = signal_rec.copy()
        new_rec.samples = filtered_samples
        new_rec.add_history(
            stage="Matched Filter",
            params={
                "pulse_shape": pulse_shape.value,
                "sps": samples_per_symbol,
                "beta": beta,
                "span": span_symbols,
            },
            elapsed_ms=0.0,
        )
        return new_rec
