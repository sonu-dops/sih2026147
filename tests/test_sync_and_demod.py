"""Unit tests for carrier sync, symbol timing, demodulation, EVM, and decoding."""

import numpy as np
import pytest

from signalinsight.amc.synthetic import SyntheticSignalGenerator
from signalinsight.core.models import SignalRecord
from signalinsight.decoding.crc import CRCValidator
from signalinsight.decoding.fec import ConfiguredFECDecoder
from signalinsight.demodulation.constellation import ConstellationAnalyzer
from signalinsight.demodulation.fsk import FSKDemodulator
from signalinsight.demodulation.psk import BPSKDemodulator, EightPSKDemodulator, QPSKDemodulator
from signalinsight.demodulation.qam import QAM16Demodulator
from signalinsight.synchronization.carrier_sync import CarrierSynchronizer, CostasLoop
from signalinsight.synchronization.timing_sync import GardnerTimingRecovery


def test_costas_loop_qpsk():
    fs = 1e6
    rec = SyntheticSignalGenerator.generate(
        modulation="QPSK",
        sample_rate=fs,
        symbol_rate=100e3,
        num_symbols=1000,
        snr_db=30.0,
        carrier_offset_hz=2000.0,  # 2 kHz CFO
        phase_offset_rad=0.5,
        seed=42,
    )

    loop = CostasLoop(order=4, loop_bandwidth=0.03)
    res = loop.process(rec.samples, sample_rate=fs)

    assert res.converged
    # CFO recovered within 15% tolerance of 2000 Hz
    assert np.isclose(res.estimated_cfo_hz, 2000.0, atol=300.0)


def test_gardner_timing_recovery():
    fs = 1e6
    rec = SyntheticSignalGenerator.generate(
        modulation="BPSK",
        sample_rate=fs,
        symbol_rate=100e3,
        num_symbols=500,
        snr_db=30.0,
        seed=101,
    )

    sps = int(fs / 100e3)
    recovery = GardnerTimingRecovery(loop_bandwidth=0.02)
    res = recovery.recover(rec.samples, samples_per_symbol=sps)

    assert len(res.symbol_samples) > 200
    assert res.converged


def test_qpsk_demodulation_evm():
    # Generate clean QPSK symbols
    np.random.seed(42)
    n_syms = 100
    b0 = np.random.randint(0, 2, n_syms)
    b1 = np.random.randint(0, 2, n_syms)
    i_vals = np.where(b1 == 0, 1.0, -1.0)
    q_vals = np.where(b0 == 0, 1.0, -1.0)
    symbols = (i_vals + 1j * q_vals) / np.sqrt(2.0)

    demod = QPSKDemodulator()
    res = demod.demodulate(symbols)

    assert res.symbol_count == n_syms
    assert len(res.bits) == 2 * n_syms
    # Perfect signal: EVM RMS should be ~0.0%
    assert res.evm_rms_pct.value < 0.1


def test_16qam_demodulation():
    demod = QAM16Demodulator()
    ideal = demod.get_ideal_constellation()
    res = demod.demodulate(ideal)

    assert res.symbol_count == 16
    assert len(res.bits) == 64
    assert res.evm_rms_pct.value < 0.01


def test_decoding_unconfigured_strict_rule():
    bits = [0, 1, 0, 1, 1, 0]
    decoder = ConfiguredFECDecoder()  # Defaults to None / Unconfigured
    res = decoder.decode(bits)

    assert not res.available
    assert "coding configuration not specified" in res.message


def test_decoding_hamming_7_4():
    # 4 data bits: [1, 0, 1, 1]
    # Hamming(7,4) codeword generator:
    # d = [d1, d2, d3, d4] -> p1 = d1^d2^d4, p2 = d1^d3^d4, p3 = d2^d3^d4
    # codeword: [p1, p2, d1, p3, d2, d3, d4]
    d = [1, 0, 1, 1]
    p1 = d[0] ^ d[1] ^ d[3]  # 1^0^1 = 0
    p2 = d[0] ^ d[2] ^ d[3]  # 1^1^1 = 1
    p3 = d[1] ^ d[2] ^ d[3]  # 0^1^1 = 0
    codeword = [p1, p2, d[0], p3, d[1], d[2], d[3]]  # [0, 1, 1, 0, 0, 1, 1]

    # Inject single bit error at index 2 (flip d1)
    corrupted = list(codeword)
    corrupted[2] ^= 1

    decoder = ConfiguredFECDecoder(fec_type="Hamming(7,4)")
    res = decoder.decode(corrupted)

    assert res.available
    assert res.bit_count == 4


def test_crc16():
    data = b"SIGNALINSIGHT_TEST_123"
    crc = CRCValidator.compute_crc16_ccitt(data)
    # Validate deterministic CRC calculation
    assert crc > 0
    crc2 = CRCValidator.compute_crc16_ccitt(data)
    assert crc == crc2


def test_blind_fec_convolutional():
    from signalinsight.decoding.fec import BlindFECEstimator
    # Generate Rate 1/2 convolutional stream (K=3, G1=[1,1,1], G2=[1,0,1])
    import numpy as np
    np.random.seed(42)
    info_bits = np.random.randint(0, 2, 60)
    interleaved = []
    reg = [0, 0]
    for b in info_bits:
        y1 = b ^ reg[0] ^ reg[1]
        y2 = b ^ reg[1]
        interleaved.extend([int(y1), int(y2)])
        reg = [b, reg[0]]

    est = BlindFECEstimator.estimate(interleaved)
    assert "convolutional" in est.detected_scheme.lower()
    assert est.code_rate == "1/2"
    assert est.confidence >= 0.70


def test_blind_fec_auto_decoder():
    from signalinsight.decoding.fec import ConfiguredFECDecoder
    # Create bitstream with alternating preamble
    bits = [1, 0] * 32 + [1, 1, 0, 0, 1, 0, 1, 1] * 10
    decoder = ConfiguredFECDecoder(fec_type="Auto")
    res = decoder.decode(bits)

    assert res.available is True
    assert res.bit_count == len(bits)
    assert res.fec_type is not None
    assert "FEC:" in res.message
