"""Tests for model training, dataset manager, and active model inference."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.db.models.amc import Model
from signalinsight.amc.classifier import XGBoostModulationClassifier
from signalinsight.amc.dataset_manager import RadioMLDatasetManager
from signalinsight.core.models import SignalRecord
from signalinsight.io.wav_loader import WavSignalLoader
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner


def test_active_model_loading_and_inference():
    """Verifies that XGBoostModulationClassifier dynamically resolves the active DB model."""
    classifier = XGBoostModulationClassifier()
    assert classifier.model is not None
    assert classifier.model_name == "RadioML2016-XGBoost"
    assert classifier.model_version == "2.0.0"


def test_dataset_manager_methods():
    """Tests RadioML dataset manager search and credential detection."""
    mgr = RadioMLDatasetManager()
    assert mgr.target_dir.exists()
    # has_kaggle_auth returns boolean
    auth_status = mgr.has_kaggle_auth()
    assert isinstance(auth_status, bool)


def test_pipeline_with_active_trained_model():
    """Runs pipeline on demo WAV and verifies result comes from trained model."""
    demo_wav = Path("samples/demo_qpsk.wav")
    assert demo_wav.exists()

    rec = WavSignalLoader().load(demo_wav)
    runner = PipelineRunner()
    result = runner.run(rec, options=PipelineOptions())

    assert result.modulation_result is not None
    assert result.modulation_result.predicted_modulation in ["QPSK", "8PSK", "BPSK"]
    assert result.modulation_result.model_name == "RadioML2016-XGBoost"
    assert result.modulation_result.model_version == "2.0.0"


def test_api_active_model_endpoint():
    """Verifies FastAPI /api/v1/models returns active trained model."""
    client = TestClient(app)
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) > 0

    active_models = [m for m in models if m["status"] == "ACTIVE"]
    assert len(active_models) >= 1
    assert active_models[0]["name"] == "RadioML2016-XGBoost"
