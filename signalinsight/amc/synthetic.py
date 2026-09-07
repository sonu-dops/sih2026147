"""Synthetic RF signal generator for BPSK, QPSK, 8PSK, 16-QAM, and FSK with realistic impairments."""

from datetime import datetime
from typing import Dict, Optional, Tuple
import numpy as np
from scipy import signal as sp_signal

from signalinsight.core.constants import MOD_16QAM, MOD_8PSK, MOD_BPSK, MOD_FSK, MOD_QPSK
from signalinsight.core.models import ProvenanceSource, SignalRecord
from signalinsight.dsp.filters import FilterEngine


class SyntheticSignalGenerator:
    """Generates ground-truth modulated signals with configurable channel impairments."""

    @staticmethod
    def generate(
        modulation: str,
        sample_rate: float = 1_000_000.0,
        symbol_rate: float = 100_000.0,
        num_symbols: int = 2000,
        snr_db: Optional[float] = 20.0,
        carrier_offset_hz: float = 0.0,
        phase_offset_rad: float = 0.0,
        rrc_beta: float = 0.35,
        center_frequency: float = 2.4e9,
        seed: Optional[int] = None,
    ) -> SignalRecord:
        """
        Generates a synthetic complex baseband SignalRecord with known ground-truth.
        Supports: BPSK, QPSK, 8PSK, 16-QAM, FSK.
        """
        if seed is not None:
            np.random.seed(seed)

        sps = int(round(sample_rate / symbol_rate))
        mod_upper = modulation.upper()

        if mod_upper == MOD_BPSK:
            symbols = 2 * np.random.randint(0, 2, num_symbols) - 1.0 + 0j
        elif mod_upper == MOD_QPSK:
            i_bits = 2 * np.random.randint(0, 2, num_symbols) - 1.0
            q_bits = 2 * np.random.randint(0, 2, num_symbols) - 1.0
            symbols = (i_bits + 1j * q_bits) / np.sqrt(2.0)
        elif mod_upper == MOD_8PSK:
            phases = np.random.randint(0, 8, num_symbols) * (2.0 * np.pi / 8.0)
            symbols = np.exp(1j * phases)
        elif mod_upper in (MOD_16QAM, "16QAM"):
            i_vals = 2 * np.random.randint(0, 4, num_symbols) - 3.0
            q_vals = 2 * np.random.randint(0, 4, num_symbols) - 3.0
            symbols = (i_vals + 1j * q_vals) / np.sqrt(10.0)
        elif mod_upper == MOD_FSK:
            # 2-FSK frequency modulation
            freq_dev = symbol_rate / 2.0  # Deviation = 0.5 * symbol_rate (continuous phase FSK)
            data_bits = 2 * np.random.randint(0, 2, num_symbols) - 1
            upsampled_freq = np.repeat(data_bits * freq_dev, sps)
            t_vec = np.arange(len(upsampled_freq)) / sample_rate
            phase = 2.0 * np.pi * np.cumsum(upsampled_freq) / sample_rate
            raw_signal = np.exp(1j * phase)
            symbols = np.array([])  # Continuous waveform
        else:
            raise ValueError(f"Unsupported modulation type: {modulation}")

        # Pulse shaping with RRC for linear modulations (BPSK, QPSK, 8PSK, 16-QAM)
        if mod_upper != MOD_FSK:
            total_samples = num_symbols * sps
            upsampled = np.zeros(total_samples, dtype=np.complex64)
            upsampled[::sps] = symbols

            rrc_taps = FilterEngine.design_rrc_filter(
                samples_per_symbol=sps,
                beta=rrc_beta,
                span_symbols=8,
            )
            raw_signal = FilterEngine.apply_filter(upsampled, rrc_taps)

        # Carrier frequency offset and phase offset
        n = len(raw_signal)
        t = np.arange(n) / sample_rate
        cfo_phase = 2.0 * np.pi * carrier_offset_hz * t + phase_offset_rad
        cfo_signal = raw_signal * np.exp(1j * cfo_phase)

        # Additive White Gaussian Noise (AWGN)
        if snr_db is not None:
            sig_power = np.mean(np.abs(cfo_signal) ** 2)
            noise_power = sig_power / (10.0 ** (snr_db / 10.0))
            noise = (
                np.random.normal(0.0, np.sqrt(noise_power / 2.0), n)
                + 1j * np.random.normal(0.0, np.sqrt(noise_power / 2.0), n)
            )
            final_signal = cfo_signal + noise
        else:
            final_signal = cfo_signal

        ground_truth = {
            "modulation": mod_upper,
            "sample_rate": sample_rate,
            "symbol_rate": symbol_rate,
            "sps": sps,
            "snr_db": snr_db,
            "carrier_offset_hz": carrier_offset_hz,
            "phase_offset_rad": phase_offset_rad,
            "rrc_beta": rrc_beta if mod_upper != MOD_FSK else None,
            "num_symbols": num_symbols,
        }

        meta_sources = {
            "sample_rate": ProvenanceSource.USER,
            "center_frequency": ProvenanceSource.USER,
        }

        return SignalRecord(
            samples=final_signal.astype(np.complex64),
            sample_rate=sample_rate,
            center_frequency=center_frequency,
            timestamp=datetime.utcnow(),
            data_type="complex64",
            channels=2,
            iq_order="IQ",
            metadata={"ground_truth": ground_truth, "is_synthetic": True},
            metadata_sources=meta_sources,
        )
