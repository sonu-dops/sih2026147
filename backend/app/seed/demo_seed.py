"""Safe development seed data generator. All demo data is explicitly tagged [DEMO]."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.database import SessionLocal, init_db
from backend.app.db.models.amc import Dataset, Model
from backend.app.db.models.project import Project
from backend.app.db.models.signal import SignalFile, SignalMetadata
from signalinsight.core.constants import SUPPORTED_MODULATIONS


def seed_demo_data(db: Optional[Session] = None) -> None:
    """Populates database with explicit DEMO records for development and testing."""
    own_session = False
    if db is None:
        init_db()
        db = SessionLocal()
        own_session = True

    try:
        # Check if DEMO project already exists
        existing_proj = db.query(Project).filter(Project.name == "[DEMO] Laboratory Bench Project").first()
        if not existing_proj:
            demo_project = Project(
                name="[DEMO] Laboratory Bench Project",
                description="[DEMO] Default engineering project for testing AMC pipelines and RF ingestion.",
                status="ACTIVE",
            )
            db.add(demo_project)
            db.commit()
            db.refresh(demo_project)
            proj_id = demo_project.id
        else:
            proj_id = existing_proj.id

        # Check default baseline model
        existing_model = db.query(Model).filter(Model.name == "XGBoost AMC Baseline").first()
        model_path = Path("signalinsight/amc/models/amc_xgboost_v1.json")
        if not existing_model:
            demo_model = Model(
                name="XGBoost AMC Baseline",
                model_type="XGBoost",
                version="1.0.0",
                file_path=str(model_path.resolve()) if model_path.exists() else "data/models/amc_xgboost_v1.json",
                feature_version="1.0.0",
                classes=list(SUPPORTED_MODULATIONS),
                metrics={"accuracy": 0.965, "f1": 0.964},
                status="ACTIVE",
            )
            db.add(demo_model)

        # Check sample dataset
        existing_dataset = db.query(Dataset).filter(Dataset.name == "[DEMO] Synthetic Constellation Benchmark").first()
        if not existing_dataset:
            demo_dataset = Dataset(
                name="[DEMO] Synthetic Constellation Benchmark",
                description="[DEMO] Synthetic RF waveforms (BPSK, QPSK, 8PSK, 16QAM, FSK) with varying SNR.",
                source="SYNTHETIC",
                version="1.0.0",
                sample_count=250,
                feature_count=18,
                classes=list(SUPPORTED_MODULATIONS),
            )
            db.add(demo_dataset)

        # Check sample signal file
        existing_sig = db.query(SignalFile).filter(SignalFile.filename == "demo_qpsk.wav").first()
        sample_wav = Path("samples/demo_qpsk.wav")
        if not existing_sig and sample_wav.exists():
            demo_sig = SignalFile(
                project_id=proj_id,
                filename="demo_qpsk.wav",
                original_path=str(sample_wav.resolve()),
                file_hash="demo_qpsk_hash_44100",
                file_size=sample_wav.stat().st_size,
                format="WAV",
                data_type="complex64",
                iq_order="IQ",
                sample_count=50000,
                sample_rate=100000.0,
                center_frequency=0.0,
                duration=0.5,
            )
            db.add(demo_sig)
            db.commit()
            db.refresh(demo_sig)

            meta = [
                SignalMetadata(
                    signal_file_id=demo_sig.id,
                    parameter_name="Modulation Hint",
                    parameter_value="QPSK",
                    unit="",
                    source="SIGMF",
                    confidence=1.0,
                ),
                SignalMetadata(
                    signal_file_id=demo_sig.id,
                    parameter_name="Sample Rate",
                    parameter_value="100000.0",
                    unit="Hz",
                    source="SIGMF",
                    confidence=1.0,
                ),
            ]
            db.add_all(meta)

        db.commit()
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    from typing import Optional
    seed_demo_data()
    print("Seed data initialized.")
