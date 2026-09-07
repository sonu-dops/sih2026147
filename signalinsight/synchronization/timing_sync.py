"""Gardner Symbol Timing Recovery with fractional interpolation."""

from typing import NamedTuple, Tuple
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord


class TimingRecoveryResult(NamedTuple):
    symbol_samples: np.ndarray  # 1 sample per symbol at strobe points
    timing_error_history: np.ndarray
    converged: bool


class GardnerTimingRecovery:
    """
    Gardner Timing Error Detector (TED) for non-data-aided symbol timing recovery.
    Operates at 2 samples per symbol to track fractional sampling phase.
    """

    def __init__(self, loop_bandwidth: float = 0.01, damping: float = 0.707):
        denom = 1.0 + 2.0 * damping * loop_bandwidth + loop_bandwidth ** 2
        self.alpha = (4.0 * damping * loop_bandwidth) / denom
        self.beta = (4.0 * loop_bandwidth ** 2) / denom

    def recover(
        self,
        samples: np.ndarray,
        samples_per_symbol: int,
    ) -> TimingRecoveryResult:
        if samples_per_symbol < 2:
            raise ValueError(f"Gardner timing recovery requires >= 2 samples per symbol, got {samples_per_symbol}")

        # Resample or decimate so that we process at nominal 2 samples per symbol
        sps = samples_per_symbol
        step = max(1, sps // 2)
        dec_samples = samples[::step]

        n = len(dec_samples)
        symbols = []
        errors = []

        mu = 0.0
        omega = 1.0  # Nominal symbol duration step in half-symbol units

        # Gardner TED requires three points: strobe k, midpoint k-1/2, previous strobe k-1
        # In half-symbol units, index stride is 2
        idx = 2
        while idx < n - 2:
            # Strobe point k
            s_curr = dec_samples[idx]
            # Midpoint k-1/2
            s_mid = dec_samples[idx - 1]
            # Previous strobe k-1
            s_prev = dec_samples[idx - 2]

            # Gardner timing error: Real{ (s_curr - s_prev) * conj(s_mid) }
            e_i = s_mid.real * (s_curr.real - s_prev.real)
            e_q = s_mid.imag * (s_curr.imag - s_prev.imag)
            error = float(np.clip(e_i + e_q, -2.0, 2.0))

            errors.append(error)
            symbols.append(s_curr)

            # Loop filter update
            omega += self.beta * error
            # Advance to next symbol strobe
            stride = int(round(2.0 * omega))
            idx += max(1, stride)

        out_symbols = np.array(symbols, dtype=np.complex64)
        err_arr = np.array(errors, dtype=np.float32)

        tail_len = max(10, int(len(err_arr) * 0.2)) if len(err_arr) > 0 else 0
        converged = bool(len(err_arr) > 0 and np.var(err_arr[-tail_len:]) < 0.3)

        return TimingRecoveryResult(
            symbol_samples=out_symbols,
            timing_error_history=err_arr,
            converged=converged,
        )
