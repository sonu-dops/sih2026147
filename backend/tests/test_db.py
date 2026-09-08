"""Tests for database connectivity, tables, and backup."""

from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.db.database import backup_database
from backend.app.db.models.amc import Classification, Dataset, Model, TrainingMetric, TrainingRun
from backend.app.db.models.analysis import AnalysisResult, AnalysisRun, Feature
from backend.app.db.models.job import ProcessingHistory, ProcessingJob
from backend.app.db.models.project import Project
from backend.app.db.models.report import AppSetting, Report
from backend.app.db.models.signal import SignalFile, SignalMetadata


def test_database_backup():
    backup_file = backup_database(backup_dir=Path("./data/backups"))
    assert backup_file.exists()
    assert backup_file.stat().st_size > 0


def test_project_and_signal_persistence(db_session: Session):
    # Create Project
    proj = Project(name="Radar Test Project", description="Bench evaluation")
    db_session.add(proj)
    db_session.commit()
    assert proj.id is not None

    # Create SignalFile
    sig = SignalFile(
        project_id=proj.id,
        filename="chirp.iq",
        file_hash="abcdef1234567890",
        file_size=1024,
        format="IQ",
        sample_rate=2000000.0,
        center_frequency=433.92e6,
        duration=0.000512,
    )
    db_session.add(sig)
    db_session.commit()
    assert sig.id is not None

    # Create SignalMetadata
    meta = SignalMetadata(
        signal_file_id=sig.id,
        parameter_name="Antenna",
        parameter_value="Yagi-Uda",
        unit="",
        source="USER",
    )
    db_session.add(meta)
    db_session.commit()
    assert meta.id is not None

    # Query relations
    fetched_proj = db_session.get(Project, proj.id)
    assert len(fetched_proj.signal_files) == 1
    assert fetched_proj.signal_files[0].filename == "chirp.iq"
    assert len(fetched_proj.signal_files[0].metadata_records) == 1
    assert fetched_proj.signal_files[0].metadata_records[0].parameter_value == "Yagi-Uda"


def test_analysis_and_classification_persistence(db_session: Session):
    sig = SignalFile(
        filename="test_psk.wav",
        file_hash="1122334455667788",
        file_size=2048,
        format="WAV",
        sample_rate=100000.0,
    )
    db_session.add(sig)
    db_session.commit()

    run = AnalysisRun(signal_file_id=sig.id, status="COMPLETED")
    db_session.add(run)
    db_session.commit()

    res = AnalysisResult(
        analysis_run_id=run.id,
        carrier_frequency=10000.0,
        occupied_bandwidth=25000.0,
        snr=18.5,
    )
    db_session.add(res)

    feat = Feature(
        analysis_run_id=run.id,
        feature_name="c42",
        feature_value=-1.02,
    )
    db_session.add(feat)

    clf = Classification(
        analysis_run_id=run.id,
        predicted_class="QPSK",
        confidence=0.985,
        class_probabilities={"QPSK": 0.985, "BPSK": 0.015},
    )
    db_session.add(clf)

    db_session.commit()

    fetched_run = db_session.get(AnalysisRun, run.id)
    assert fetched_run.result.carrier_frequency == 10000.0
    assert len(fetched_run.features) == 1
    assert fetched_run.features[0].feature_name == "c42"
    assert fetched_run.classification.predicted_class == "QPSK"
