"""Unit tests for DSP algorithms and transformations."""

import numpy as np
import pytest

from signalinsight.core.models import SignalRecord
from signalinsight.dsp.analytic import AnalyticSignalEngine
from signalinsight.dsp.fft import FFTEngine
from signalinsight.dsp.filters import FilterEngine, PulseShape
from signalinsight.dsp.preprocessing import NormalizationMode, SignalPreprocessor
from signalinsight.dsp.psd import PSDEngine
from signalinsight.dsp.spectrogram import SpectrogramEngine


def test_dc_offset_removal():
    n = 2000
    t = np.linspace(0, 1.0, n, endpoint=False)
    # AC signal + known DC offset (I_dc = 1.5, Q_dc = -0.8)
    clean_i = np.cos(2 * np.pi * 50 * t)
    clean_q = np.sin(2 * np.pi * 50 * t)
    sig_with_dc = (clean_i + 1.5) + 1j * (clean_q - 0.8)

    rec = SignalRecord(samples=sig_with_dc, sample_rate=1000.0)
    corrected_rec, dc_res = SignalPreprocessor.remove_dc_offset(rec)

    assert np.isclose(dc_res.offset_i, 1.5, atol=1e-3)
    assert np.isclose(dc_res.offset_q, -0.8, atol=1e-3)
    # Corrected signal mean must be near zero
    assert np.isclose(np.mean(corrected_rec.samples.real), 0.0, atol=1e-6)
    assert np.isclose(np.mean(corrected_rec.samples.imag), 0.0, atol=1e-6)


def test_normalization():
    samples = np.array([3.0 + 4j, -3.0 - 4j, 3.0 - 4j, -3.0 + 4j], dtype=np.complex64)
    rec = SignalRecord(samples=samples, sample_rate=100.0)

    # RMS normalization
    norm_rms_rec = SignalPreprocessor.normalize(rec, mode=NormalizationMode.RMS)
    rms_val = SignalPreprocessor.calculate_rms(norm_rms_rec.samples)
    assert np.isclose(rms_val, 1.0, atol=1e-6)

    # Peak normalization
    norm_peak_rec = SignalPreprocessor.normalize(rec, mode=NormalizationMode.PEAK)
    peak_val = np.max(np.abs(norm_peak_rec.samples))
    assert np.isclose(peak_val, 1.0, atol=1e-6)


def test_rrc_filter():
    sps = 4
    beta = 0.35
    taps = FilterEngine.design_rrc_filter(samples_per_symbol=sps, beta=beta, span_symbols=6)
    assert len(taps) == 6 * sps + 1
    # Unit energy
    assert np.isclose(np.sum(taps ** 2), 1.0, atol=1e-5)
    # Symmetry: taps should be symmetric around center
    assert np.allclose(taps, taps[::-1], atol=1e-8)


def test_analytic_signal_properties():
    fs = 10000.0
    f0 = 500.0
    t = np.arange(2000) / fs
    # Pure tone
    real_sig = np.cos(2 * np.pi * f0 * t)

    props = AnalyticSignalEngine.compute_properties(real_sig, sample_rate=fs)
    # Envelope of cos(2*pi*f0*t) should be ~1.0 in the reliable region
    reliable_env = props.envelope[props.reliable_mask]
    assert np.allclose(reliable_env, 1.0, atol=0.05)

    # Instantaneous frequency in reliable region should be ~500 Hz
    reliable_f_inst = props.instantaneous_frequency[props.reliable_mask]
    assert np.allclose(reliable_f_inst, f0, atol=5.0)


def test_fft_peak_interpolation():
    fs = 100000.0
    f_carrier = 12345.0  # Off-grid frequency
    n = 2048
    t = np.arange(n) / fs
    # Complex tone
    tone = np.exp(1j * 2 * np.pi * f_carrier * t)

    spec = FFTEngine.compute_spectrum(tone, sample_rate=fs, fft_size=n, window_name="Hann")
    # Sub-bin interpolation should achieve accurate peak frequency estimation
    assert np.isclose(spec.peak_frequency, f_carrier, atol=fs / (2 * n))


def test_psd_total_power():
    fs = 10000.0
    n = 4096
    t = np.arange(n) / fs
    # Unit amplitude complex sinusoid: power = 1.0
    sig = np.exp(1j * 2 * np.pi * 1000.0 * t)
    psd_res = PSDEngine.compute_psd(sig, sample_rate=fs, nperseg=512)
    assert np.isclose(psd_res.total_power, 1.0, rtol=0.1)


def test_spectrogram():
    fs = 10000.0
    n = 2000
    sig = np.random.randn(n) + 1j * np.random.randn(n)
    spec_res = SpectrogramEngine.compute_spectrogram(sig, sample_rate=fs, nperseg=256)
    assert spec_res.spectrogram_db.ndim == 2
    assert spec_res.spectrogram_db.shape[0] == 256
    assert len(spec_res.times) == spec_res.spectrogram_db.shape[1]
