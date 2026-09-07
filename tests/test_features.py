"""Unit tests for statistical, spectral, and higher-order cumulant features."""

import numpy as np
import pytest

from signalinsight.core.models import SignalRecord
from signalinsight.features.cumulants import CumulantsCalculator
from signalinsight.features.extractor import FeatureExtractor


def test_cumulants_gaussian_noise():
    # For zero-mean complex Gaussian noise, theoretical fourth-order cumulants C40 = 0 and C42 = 0
    np.random.seed(42)
    n = 50000
    noise = (np.random.randn(n) + 1j * np.random.randn(n)) / np.sqrt(2)
    res = CumulantsCalculator.compute(noise)

    # Normalized invariants f40 and f42 should be close to 0 for Gaussian noise
    assert res.f40 < 0.15
    assert res.f42 < 0.15


def test_cumulants_qpsk():
    # For QPSK constellation: {1+j, 1-j, -1+j, -1-j} / sqrt(2)
    # Every symbol has x^4 = -1, so E[x^4] = -1.
    # Theoretical: C20 = 0 -> C40 = E[x^4] - 3*(C20)^2 = -1 -> f40 = 1.0
    # C42 = E[|x|^4] - |C20|^2 - 2*(C21)^2 = 1 - 0 - 2 = -1 -> f42 = 1.0
    np.random.seed(42)
    n = 20000
    bits_i = 2 * np.random.randint(0, 2, n) - 1
    bits_q = 2 * np.random.randint(0, 2, n) - 1
    qpsk_symbols = (bits_i + 1j * bits_q) / np.sqrt(2.0)

    res = CumulantsCalculator.compute(qpsk_symbols)
    assert np.isclose(res.f40, 1.0, atol=0.08)
    assert np.isclose(res.f42, 1.0, atol=0.08)


def test_cumulants_bpsk():
    # For BPSK constellation: {+1, -1}
    # Theoretical: C20 = 1, C21 = 1
    # C40 = E[x^4] - 3(C20)^2 = 1 - 3 = -2 -> f40 = 2.0
    # C42 = E[x^4] - |C20|^2 - 2(C21)^2 = 1 - 1 - 2 = -2 -> f42 = 2.0
    np.random.seed(42)
    n = 20000
    bpsk_symbols = (2 * np.random.randint(0, 2, n) - 1).astype(np.complex64)

    res = CumulantsCalculator.compute(bpsk_symbols)
    assert np.isclose(res.f40, 2.0, atol=0.08)
    assert np.isclose(res.f42, 2.0, atol=0.08)


def test_feature_extractor():
    fs = 1e6
    n = 4096
    samples = np.random.randn(n) + 1j * np.random.randn(n)
    rec = SignalRecord(samples=samples, sample_rate=fs)

    extracted = FeatureExtractor.extract_all(rec)
    assert len(extracted.all_features) >= 15
    assert len(extracted.ml_feature_vector) == len(FeatureExtractor.FEATURE_VECTOR_KEYS)
    assert not np.isnan(extracted.ml_feature_vector).any()
    assert not np.isinf(extracted.ml_feature_vector).any()
