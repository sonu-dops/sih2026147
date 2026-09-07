"""FSK demodulator using frequency discriminator."""

from typing import Dict, List
import numpy as np

from signalinsight.core.models import DemodulationResult
from signalinsight.demodulation.base import BaseDemodulator
from signalinsight.dsp.analytic import AnalyticSignalEngine


class FSKDemodulator(BaseDemodulator):
    """Frequency discriminator demodulator for 2-FSK signals."""

    def __init__(self, sample_rate: float = 1e6, symbol_rate: float = 100e3):
        self.sample_rate = sample_rate
        self.symbol_rate = symbol_rate

    def get_ideal_constellation(self) -> np.ndarray:
        # Constant envelope circle
        angles = np.linspace(0, 2 * np.pi, 32, endpoint=False)
        return np.exp(1j * angles).astype(np.complex64)

    def get_symbol_mapping(self) -> Dict[int, complex]:
        return {0: 1.0 + 0j, 1: -1.0 + 0j}

    def demodulate(self, symbols: np.ndarray) -> DemodulationResult:
        # For FSK, input is typically raw waveform or oversampled symbols
        props = AnalyticSignalEngine.compute_properties(symbols, sample_rate=self.sample_rate)
        f_inst = props.instantaneous_frequency

        # Downsample to nominal symbol centers
        sps = max(1, int(round(self.sample_rate / self.symbol_rate)))
        sampled_freq = f_inst[sps // 2 :: sps]

        # Decision based on sign of frequency deviation relative to center
        f_center = np.median(sampled_freq)
        bits = [1 if f > f_center else 0 for f in sampled_freq]

        return DemodulationResult(
            modulation="FSK",
            symbol_count=len(bits),
            symbols=list(symbols[:len(bits)]),
            bits=bits,
            notes=f"2-FSK Frequency Discriminator: Center={f_center:,.1f} Hz",
        )
