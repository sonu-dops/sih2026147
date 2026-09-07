"""16-QAM demodulator with rectangular decision regions and Gray coding."""

from typing import Dict, List
import numpy as np

from signalinsight.core.models import DemodulationResult
from signalinsight.demodulation.base import BaseDemodulator
from signalinsight.demodulation.constellation import ConstellationAnalyzer


class QAM16Demodulator(BaseDemodulator):
    """16-QAM Demodulator with 4 bits/symbol and square decision grid."""

    def get_ideal_constellation(self) -> np.ndarray:
        levels = np.array([-3.0, -1.0, 1.0, 3.0]) / np.sqrt(10.0)
        points = []
        for i_lvl in levels:
            for q_lvl in levels:
                points.append(i_lvl + 1j * q_lvl)
        return np.array(points, dtype=np.complex64)

    def get_symbol_mapping(self) -> Dict[int, complex]:
        ideal = self.get_ideal_constellation()
        return {i: complex(pt) for i, pt in enumerate(ideal)}

    def demodulate(self, symbols: np.ndarray) -> DemodulationResult:
        n = len(symbols)
        # Normalize received symbols to average power = 1.0
        p_avg = np.mean(np.abs(symbols) ** 2)
        norm_syms = symbols / np.sqrt(max(p_avg, 1e-12))

        # Scale by sqrt(10) so levels are nominally at [-3, -1, +1, +3]
        scaled_syms = norm_syms * np.sqrt(10.0)

        # 2-bit Gray mapping for 1D levels [-3, -1, 1, 3]:
        # -3 -> [0, 0]
        # -1 -> [0, 1]
        # +1 -> [1, 1]
        # +3 -> [1, 0]
        def slice_level(val: float) -> List[int]:
            if val < -2.0:
                return [0, 0]
            elif val < 0.0:
                return [0, 1]
            elif val < 2.0:
                return [1, 1]
            else:
                return [1, 0]

        bits: List[int] = []
        for s in scaled_syms:
            b_i = slice_level(s.real)
            b_q = slice_level(s.imag)
            bits.extend(b_i + b_q)

        ideal = self.get_ideal_constellation()
        metrics = ConstellationAnalyzer.analyze(symbols, ideal)

        return DemodulationResult(
            modulation="16-QAM",
            symbol_count=n,
            symbols=list(symbols),
            bits=bits,
            evm_rms_pct=metrics.evm_rms_pct,
            evm_peak_pct=metrics.evm_peak_pct,
            notes="Standard rectangular 16-QAM decision grid with Gray mapping",
        )
