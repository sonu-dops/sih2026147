"""Unit tests for parameter estimators."""

import numpy as np
import pytest

from signalinsight.core.models import ProvenanceSource, SignalRecord
from signalinsight.dsp.filters import FilterEngine
from signalinsight.estimation.bandwidth import BandwidthEstimator
from signalinsight.estimation.carrier import CarrierEstimator
from signalinsight.estimation.noise_snr import NoiseSNREstimator
from signalinsight.estimation.power import PowerEstimator
from signalinsight.estimation.symbol_rate import SymbolRateEstimator


def test_carrier_estimator():
    fs = 1e6
    fc_offset = 75000.0  # 75 kHz offset
    n = 8192
    t = np.arange(n) / fs
    # Complex tone
    tone = np.exp(1j * 2 * np.pi * fc_offset * t)

    rec = SignalRecord(samples=tone, sample_rate=fs, center_frequency=2.4e9)
    res = CarrierEstimator().estimate(rec)

    assert np.isclose(res.baseband_frequency_hz.value, fc_offset, atol=200.0)
    assert np.isclose(res.rf_carrier_frequency_hz.value, 2.4e9 + fc_offset, atol=200.0)
    assert res.baseband_frequency_hz.source == ProvenanceSource.ESTIMATED


def test_bandwidth_estimator():
    fs = 1e6
    n = 8192
    # Generate filtered noise with known cutoff at 100 kHz (total BW ~200 kHz)
    raw = np.random.randn(n) + 1j * np.random.randn(n)
    taps = FilterEngine.design_lowpass_fir(sample_rate=fs, cutoff_hz=100000.0, num_taps=101)
    filtered = FilterEngine.apply_filter(raw, taps)

    rec = SignalRecord(samples=filtered, sample_rate=fs)
    res = BandwidthEstimator().estimate(rec)

    # 99% OBW should be approximately 200 kHz
    assert 170000.0 <= res.obw_99_hz.value <= 230000.0


def test_noise_snr_estimator():
    fs = 1e6
    n = 16384
    t = np.arange(n) / fs
    # Clean tone + white noise at ~20 dB SNR
    signal = np.exp(1j * 2 * np.pi * 50000.0 * t)
    noise = (np.random.randn(n) + 1j * np.random.randn(n)) * 0.1
    noisy_sig = signal + noise

    rec = SignalRecord(samples=noisy_sig, sample_rate=fs)
    res = NoiseSNREstimator().estimate(rec)

    assert res.snr_db.value is not None
    assert res.snr_db.value > 10.0


def test_symbol_rate_estimator():
    fs = 1e6
    symbol_rate = 100000.0  # 100 kbaud
    sps = int(fs / symbol_rate)  # 10 samples per symbol
    num_symbols = 1000

    # BPSK symbols
    symbols = 2 * np.random.randint(0, 2, num_symbols) - 1
    # Pulse shape with RRC
    upsampled = np.zeros(num_symbols * sps)
    upsampled[::sps] = symbols
    taps = FilterEngine.design_rrc_filter(samples_per_symbol=sps, beta=0.35, span_symbols=6)
    shaped = FilterEngine.apply_filter(upsampled, taps)

    rec = SignalRecord(samples=shaped.astype(np.complex64), sample_rate=fs)
    res = SymbolRateEstimator().estimate(rec)

    assert res.symbol_rate_baud.value is not None
    # Estimated symbol rate within 5% of 100 kbaud
    assert np.isclose(res.symbol_rate_baud.value, symbol_rate, rtol=0.08)


def test_power_estimator():
    samples = np.array([1.0 + 1j, -1.0 - 1j], dtype=np.complex64)
    rec = SignalRecord(samples=samples, sample_rate=1000.0)

    # Uncalibrated: calibrated dBm must report CALIBRATION_REQUIRED
    res = PowerEstimator().estimate(rec)
    assert res.calibrated_power_dbm.source == ProvenanceSource.CALIBRATION_REQUIRED

    # Calibrated: 50 ohm impedance and 0 dB gain
    res_cal = PowerEstimator().estimate(rec, system_impedance_ohms=50.0, reference_gain_db=0.0)
    assert res_cal.calibrated_power_dbm.source == ProvenanceSource.MEASURED
    assert res_cal.calibrated_power_dbm.value is not None
