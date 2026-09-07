"""PSK demodulators: BPSK, QPSK, and 8PSK with Gray coding."""

from typing import Dict, List, Tuple
import numpy as np

from signalinsight.core.models import DemodulationResult
from signalinsight.demodulation.base import BaseDemodulator
from signalinsight.demodulation.constellation import ConstellationAnalyzer


class BPSKDemodulator(BaseDemodulator):
    """BPSK Demodulator with Gray coding: symbol 0 -> +1, symbol 1 -> -1."""

    def get_ideal_constellation(self) -> np.ndarray:
        return np.array([1.0 + 0j, -1.0 + 0j], dtype=np.complex64)

    def get_symbol_mapping(self) -> Dict[int, complex]:
        return {0: 1.0 + 0j, 1: -1.0 + 0j}

    def demodulate(self, symbols: np.ndarray) -> DemodulationResult:
        n = len(symbols)
        # Decision along I axis
        bits = [0 if s.real >= 0 else 1 for s in symbols]

        ideal = self.get_ideal_constellation()
        metrics = ConstellationAnalyzer.analyze(symbols, ideal)

        return DemodulationResult(
            modulation="BPSK",
            symbol_count=n,
            symbols=list(symbols),
            bits=bits,
            evm_rms_pct=metrics.evm_rms_pct,
            evm_peak_pct=metrics.evm_peak_pct,
            notes="Gray-coded BPSK: I >= 0 -> 0, I < 0 -> 1",
        )


class QPSKDemodulator(BaseDemodulator):
    """QPSK Demodulator with standard Gray coding."""

    def get_ideal_constellation(self) -> np.ndarray:
        scale = 1.0 / np.sqrt(2.0)
        return np.array(
            [
                (1.0 + 1j) * scale,   # 00
                (-1.0 + 1j) * scale,  # 01
                (-1.0 - 1j) * scale,  # 11
                (1.0 - 1j) * scale,   # 10
            ],
            dtype=np.complex64,
        )

    def get_symbol_mapping(self) -> Dict[int, complex]:
        scale = 1.0 / np.sqrt(2.0)
        return {
            0: (1.0 + 1j) * scale,   # 00
            1: (-1.0 + 1j) * scale,  # 01
            3: (-1.0 - 1j) * scale,  # 11
            2: (1.0 - 1j) * scale,   # 10
        }

    def demodulate(self, symbols: np.ndarray) -> DemodulationResult:
        n = len(symbols)
        bits: List[int] = []

        for s in symbols:
            # Gray mapping decisions:
            # bit 0: Q >= 0 -> 0, Q < 0 -> 1
            # bit 1: I >= 0 -> 0, I < 0 -> 1
            b0 = 0 if s.imag >= 0 else 1
            b1 = 0 if s.real >= 0 else 1
            bits.extend([b0, b1])

        ideal = self.get_ideal_constellation()
        metrics = ConstellationAnalyzer.analyze(symbols, ideal)

        return DemodulationResult(
            modulation="QPSK",
            symbol_count=n,
            symbols=list(symbols),
            bits=bits,
            evm_rms_pct=metrics.evm_rms_pct,
            evm_peak_pct=metrics.evm_peak_pct,
            notes="Gray-coded QPSK decision in 4 quadrants",
        )


class EightPSKDemodulator(BaseDemodulator):
    """8PSK Demodulator with Gray coding around unit circle."""

    def get_ideal_constellation(self) -> np.ndarray:
        angles = np.arange(8) * (2.0 * np.pi / 8.0)
        return np.exp(1j * angles).astype(np.complex64)

    def get_symbol_mapping(self) -> Dict[int, complex]:
        angles = np.arange(8) * (2.0 * np.pi / 8.0)
        return {i: complex(np.exp(1j * angles[i])) for i in range(8)}

    def demodulate(self, symbols: np.ndarray) -> DemodulationResult:
        n = len(symbols)
        ideal = self.get_ideal_constellation()
        # Find closest angle
        angles = (np.angle(symbols) + 2.0 * np.pi) % (2.0 * np.pi)
        sector = (np.round(angles / (np.pi / 4.0)).astype(int)) % 8

        # 3-bit Gray mapping table
        gray_table = {
            0: [0, 0, 0],
            1: [0, 0, 1],
            2: [0, 1, 1],
            3: [0, 1, 0],
            4: [1, 1, 0],
            5: [1, 1, 1],
            6: [1, 0, 1],
            7: [1, 0, 0],
        }

        bits: List[int] = []
        for s_idx in sector:
            bits.extend(gray_table[s_idx])

        metrics = ConstellationAnalyzer.analyze(symbols, ideal)

        return DemodulationResult(
            modulation="8PSK",
            symbol_count=n,
            symbols=list(symbols),
            bits=bits,
            evm_rms_pct=metrics.evm_rms_pct,
            evm_peak_pct=metrics.evm_peak_pct,
            notes="Gray-coded 8PSK sector slicing",
        )
