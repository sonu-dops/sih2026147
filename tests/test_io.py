"""Unit tests for SignalInsight I/O and validation subsystem."""

import json
from pathlib import Path
import numpy as np
import pytest
from scipy.io import wavfile

from signalinsight.core.exceptions import FileValidationError, NumericalInstabilityError
from signalinsight.core.models import ProvenanceSource
from signalinsight.io.iq_loader import RawIQSignalLoader
from signalinsight.io.project import ProjectFile, ProjectManager
from signalinsight.io.sigmf_loader import SigMFSignalLoader
from signalinsight.io.validator import SignalValidator
from signalinsight.io.wav_loader import WavSignalLoader


def test_validator_file_errors(tmp_path: Path):
    non_existent = tmp_path / "non_existent.iq"
    with pytest.raises(FileValidationError):
        SignalValidator.validate_file(non_existent)

    empty_file = tmp_path / "empty.iq"
    empty_file.write_bytes(b"")
    with pytest.raises(FileValidationError):
        SignalValidator.validate_file(empty_file)


def test_validator_nan_inf():
    clean = np.array([1.0 + 1j, 2.0 - 1j], dtype=np.complex64)
    SignalValidator.validate_samples(clean)

    with_nan = np.array([1.0 + 1j, np.nan + 0j], dtype=np.complex64)
    with pytest.raises(NumericalInstabilityError):
        SignalValidator.validate_samples(with_nan)

    with_inf = np.array([1.0 + 1j, np.inf + 0j], dtype=np.complex64)
    with pytest.raises(NumericalInstabilityError):
        SignalValidator.validate_samples(with_inf)


def test_wav_loader_stereo_iq(tmp_path: Path):
    fs = 48000
    t = np.linspace(0, 0.1, int(fs * 0.1), endpoint=False)
    i_signal = np.cos(2 * np.pi * 1000 * t).astype(np.float32)
    q_signal = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    stereo = np.column_stack([i_signal, q_signal])

    wav_path = tmp_path / "test_stereo.wav"
    wavfile.write(wav_path, fs, stereo)

    loader = WavSignalLoader()
    assert loader.can_load(wav_path)

    meta = loader.inspect_metadata(wav_path)
    assert meta["sample_rate"] == 48000
    assert meta["channels"] == 2
    assert meta["is_complex"] is True

    record = loader.load(wav_path)
    assert record.is_complex
    assert record.sample_rate == 48000
    assert len(record.samples) == len(t)
    assert record.channels == 2
    assert np.allclose(record.samples.real, i_signal, atol=1e-5)
    assert np.allclose(record.samples.imag, q_signal, atol=1e-5)


def test_raw_iq_loader_float32(tmp_path: Path):
    num_samples = 1000
    i_data = np.cos(np.linspace(0, 10, num_samples, dtype=np.float32))
    q_data = np.sin(np.linspace(0, 10, num_samples, dtype=np.float32))
    interleaved = np.empty((num_samples * 2,), dtype=np.float32)
    interleaved[0::2] = i_data
    interleaved[1::2] = q_data

    iq_path = tmp_path / "signal.iq"
    iq_path.write_bytes(interleaved.tobytes())

    loader = RawIQSignalLoader()
    assert loader.can_load(iq_path)

    record = loader.load(
        iq_path,
        sample_rate=1e6,
        center_frequency=2.4e9,
        data_type="float32",
        iq_order="IQ",
    )

    assert record.is_complex
    assert record.sample_rate == 1e6
    assert record.center_frequency == 2.4e9
    assert len(record.samples) == num_samples
    assert np.allclose(record.samples.real, i_data, atol=1e-5)
    assert np.allclose(record.samples.imag, q_data, atol=1e-5)


def test_raw_iq_loader_int16(tmp_path: Path):
    num_samples = 500
    i_raw = np.array([10000, -10000, 20000, -20000], dtype=np.int16)
    q_raw = np.array([5000, -5000, 15000, -15000], dtype=np.int16)
    interleaved = np.empty((8,), dtype=np.int16)
    interleaved[0::2] = i_raw
    interleaved[1::2] = q_raw

    iq_path = tmp_path / "int16_test.raw"
    iq_path.write_bytes(interleaved.tobytes())

    loader = RawIQSignalLoader()
    record = loader.load(
        iq_path,
        sample_rate=500e3,
        data_type="int16",
        iq_order="IQ",
    )

    assert record.is_complex
    assert len(record.samples) == 4
    # Scaled to [-1, 1]
    assert np.allclose(record.samples.real, i_raw / 32768.0, atol=1e-4)


def test_sigmf_loader(tmp_path: Path):
    num_samples = 200
    iq = (np.ones(num_samples, dtype=np.float32) + 1j * np.zeros(num_samples, dtype=np.float32))
    interleaved = np.empty(num_samples * 2, dtype=np.float32)
    interleaved[0::2] = iq.real
    interleaved[1::2] = iq.imag

    data_path = tmp_path / "test.sigmf-data"
    meta_path = tmp_path / "test.sigmf-meta"
    data_path.write_bytes(interleaved.tobytes())

    meta = {
        "global": {
            "core:datatype": "cf32_le",
            "core:sample_rate": 2000000.0,
            "core:version": "1.0.0",
        },
        "captures": [
            {
                "core:sample_start": 0,
                "core:frequency": 915000000.0,
                "core:datetime": "2026-09-06T12:00:00Z",
            }
        ],
    }
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    loader = SigMFSignalLoader()
    assert loader.can_load(meta_path)
    assert loader.can_load(data_path)

    record = loader.load(meta_path)
    assert record.is_complex
    assert record.sample_rate == 2000000.0
    assert record.center_frequency == 915000000.0
    assert record.metadata_sources["sample_rate"] == ProvenanceSource.SIGMF
    assert record.metadata_sources["center_frequency"] == ProvenanceSource.SIGMF


def test_project_manager_save_load(tmp_path: Path):
    proj_path = tmp_path / "test_session.siproj"
    proj = ProjectFile()
    proj.metadata.name = "RF Lab Session 1"
    proj.signal_files.append("test_signal.iq")
    proj.active_signal_file = "test_signal.iq"

    ProjectManager.save_project(proj, proj_path)
    assert proj_path.exists()

    loaded = ProjectManager.load_project(proj_path)
    assert loaded.metadata.name == "RF Lab Session 1"
    assert loaded.active_signal_file == "test_signal.iq"
