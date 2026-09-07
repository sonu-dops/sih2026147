"""Unit tests for AMC classifier and synthetic signal generation."""

from pathlib import Path
import numpy as np
import pytest

from signalinsight.amc.classifier import XGBoostModulationClassifier
from signalinsight.amc.synthetic import SyntheticSignalGenerator
from signalinsight.core.constants import MOD_16QAM, MOD_8PSK, MOD_BPSK, MOD_FSK, MOD_QPSK, MOD_UNCERTAIN


def test_synthetic_generator():
    for mod in [MOD_BPSK, MOD_QPSK, MOD_8PSK, MOD_16QAM, MOD_FSK]:
        rec = SyntheticSignalGenerator.generate(
            modulation=mod,
            sample_rate=1e6,
            symbol_rate=100e3,
            num_symbols=500,
            snr_db=25.0,
            seed=123,
        )
        assert rec.is_complex
        assert len(rec.samples) > 1000
        assert rec.metadata["ground_truth"]["modulation"] == mod


def test_amc_classifier_training_and_prediction(tmp_path: Path):
    classifier = XGBoostModulationClassifier()
    # Fast training with small sample count
    classifier.train_baseline(num_samples_per_class=40, seed=42)

    # Save and reload test
    model_file = tmp_path / "test_model.json"
    classifier.save(model_file)
    assert model_file.exists()

    loaded_classifier = XGBoostModulationClassifier(model_path=model_file)

    # Test BPSK prediction
    bpsk_sig = SyntheticSignalGenerator.generate(
        modulation=MOD_BPSK,
        sample_rate=1e6,
        symbol_rate=100e3,
        num_symbols=1500,
        snr_db=25.0,
        seed=999,
    )
    res_bpsk = loaded_classifier.predict(bpsk_sig)
    assert res_bpsk.predicted_modulation == MOD_BPSK
    assert res_bpsk.confidence > 0.65

    # Test QPSK prediction
    qpsk_sig = SyntheticSignalGenerator.generate(
        modulation=MOD_QPSK,
        sample_rate=1e6,
        symbol_rate=100e3,
        num_symbols=1500,
        snr_db=25.0,
        seed=888,
    )
    res_qpsk = loaded_classifier.predict(qpsk_sig)
    assert res_qpsk.predicted_modulation == MOD_QPSK
    assert res_qpsk.confidence > 0.65

    # Test FSK prediction
    fsk_sig = SyntheticSignalGenerator.generate(
        modulation=MOD_FSK,
        sample_rate=1e6,
        symbol_rate=100e3,
        num_symbols=1500,
        snr_db=25.0,
        seed=777,
    )
    res_fsk = loaded_classifier.predict(fsk_sig)
    assert res_fsk.predicted_modulation == MOD_FSK
    assert res_fsk.confidence > 0.65


def test_amc_uncertain_threshold():
    classifier = XGBoostModulationClassifier()
    classifier.train_baseline(num_samples_per_class=30, seed=42)

    # Pure noise should have dispersed probabilities or lower confidence
    pure_noise = (np.random.randn(5000) + 1j * np.random.randn(5000)).astype(np.complex64)
    from signalinsight.core.models import SignalRecord
    noise_rec = SignalRecord(samples=pure_noise, sample_rate=1e6)

    # With very strict threshold 0.99, it should trigger UNCERTAIN
    res = classifier.predict(noise_rec, confidence_threshold=0.99)
    assert res.predicted_modulation == MOD_UNCERTAIN
    assert len(res.warnings) > 0
