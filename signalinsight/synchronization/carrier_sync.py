"""Costas Loop and Phase-Locked Loop (PLL) carrier frequency & phase recovery."""

import time
from typing import NamedTuple, Tuple
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord, SynchronizationResult


class CostasLoopResult(NamedTuple):
    synchronized_samples: np.ndarray
    estimated_cfo_hz: float
    estimated_phase_rad: float
    converged: bool
    phase_history: np.ndarray
    error_history: np.ndarray


class CostasLoop:
    """
    Decision-directed Costas loop for carrier frequency offset (CFO)
    and phase jitter tracking in BPSK, QPSK, and QAM signals.
    """

    def __init__(
        self,
        order: int = 4,
        loop_bandwidth: float = 0.01,
        damping_factor: float = 0.707,
    ):
        self.order = order  # 2 for BPSK, 4 for QPSK / QAM
        # Standard 2nd order loop filter gains (proportional alpha, integral beta)
        denom = 1.0 + 2.0 * damping_factor * loop_bandwidth + loop_bandwidth ** 2
        self.alpha = (4.0 * damping_factor * loop_bandwidth) / denom
        self.beta = (4.0 * loop_bandwidth ** 2) / denom

    def process(self, samples: np.ndarray, sample_rate: float) -> CostasLoopResult:
        n = len(samples)
        out_samples = np.zeros(n, dtype=np.complex64)
        phase_history = np.zeros(n, dtype=np.float32)
        error_history = np.zeros(n, dtype=np.float32)

        current_phase = 0.0
        current_freq = 0.0

        for i in range(n):
            # Derotate input by current NCO phase estimate
            sample = samples[i] * np.exp(-1j * current_phase)
            out_samples[i] = sample
            phase_history[i] = current_phase

            # Phase Error Detector (PED)
            i_val = sample.real
            q_val = sample.imag

            if self.order == 2:
                # BPSK PED: I * Q
                error = float(np.clip(i_val * q_val, -1.0, 1.0))
            else:
                # QPSK / QAM Decision-Directed PED: sign(I)*Q - sign(Q)*I
                i_decision = 1.0 if i_val >= 0 else -1.0
                q_decision = 1.0 if q_val >= 0 else -1.0
                error = float(np.clip(i_decision * q_val - q_decision * i_val, -2.0, 2.0))

            error_history[i] = error

            # PI Loop Filter
            current_freq += self.beta * error
            current_phase += current_freq + self.alpha * error
            # Wrap phase to [-pi, pi]
            current_phase = (current_phase + np.pi) % (2.0 * np.pi) - np.pi

        # Estimate final CFO from accumulated frequency step: rad/sample -> Hz
        estimated_cfo_hz = float((current_freq * sample_rate) / (2.0 * np.pi))
        estimated_phase = float(current_phase)

        # Convergence metric: error variance in the last 20% of samples
        tail_len = max(32, int(n * 0.2))
        tail_err_var = float(np.var(error_history[-tail_len:]))
        converged = tail_err_var < 0.25

        return CostasLoopResult(
            synchronized_samples=out_samples,
            estimated_cfo_hz=estimated_cfo_hz,
            estimated_phase_rad=estimated_phase,
            converged=converged,
            phase_history=phase_history,
            error_history=error_history,
        )


class CarrierSynchronizer:
    """Orchestrates carrier synchronization and packages result models."""

    @classmethod
    def synchronize(
        cls,
        signal_rec: SignalRecord,
        modulation: str = "QPSK",
        loop_bandwidth: float = 0.01,
    ) -> Tuple[SignalRecord, SynchronizationResult]:
        t0 = time.perf_counter()
        order = 2 if modulation.upper() == "BPSK" else 4
        loop = CostasLoop(order=order, loop_bandwidth=loop_bandwidth)
        res = loop.process(signal_rec.samples, sample_rate=signal_rec.sample_rate)
        elapsed = (time.perf_counter() - t0) * 1000.0

        new_rec = signal_rec.copy()
        new_rec.samples = res.synchronized_samples
        new_rec.add_history(
            stage="Carrier Synchronization",
            params={"modulation": modulation, "order": order, "cfo_hz": res.estimated_cfo_hz},
            elapsed_ms=elapsed,
            notes=f"Costas loop {'converged' if res.converged else 'unlocked'}",
        )

        conf = 0.92 if res.converged else 0.40
        quality = QualityLevel.HIGH if res.converged else QualityLevel.LOW

        sync_result = SynchronizationResult(
            converged=res.converged,
            carrier_frequency_offset_hz=ParameterValue(
                name="Carrier Frequency Offset",
                value=res.estimated_cfo_hz,
                unit="Hz",
                source=ProvenanceSource.CALCULATED,
                method=f"{order}th-Order Costas Loop",
                confidence=conf,
                quality=quality,
            ),
            phase_offset_rad=ParameterValue(
                name="Carrier Phase Offset",
                value=res.estimated_phase_rad,
                unit="rad",
                source=ProvenanceSource.CALCULATED,
                method="Loop NCO Accumulator",
                confidence=conf,
                quality=quality,
            ),
            timing_offset_samples=ParameterValue(
                name="Timing Offset",
                value=0.0,
                unit="samples",
                source=ProvenanceSource.UNAVAILABLE,
            ),
            algorithm=f"Costas Loop (Order={order})",
            notes=f"Final loop error variance: {float(np.var(res.error_history[-100:])):.4f}",
        )

        return new_rec, sync_result
