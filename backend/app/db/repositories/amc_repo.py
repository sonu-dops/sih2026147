"""AMC and ML models repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.amc import Classification, Dataset, Model, TrainingMetric, TrainingRun
from backend.app.db.repositories.base import BaseRepository


class AMCRepository:
    def __init__(self, db: Session):
        self.db = db

    # Classifications
    def save_classification(self, classification: Classification) -> Classification:
        self.db.add(classification)
        self.db.commit()
        self.db.refresh(classification)
        return classification

    def get_classification_by_run(self, analysis_run_id: int) -> Optional[Classification]:
        stmt = select(Classification).where(Classification.analysis_run_id == analysis_run_id)
        return self.db.scalars(stmt).first()

    # Models
    def list_models(self) -> List[Model]:
        stmt = select(Model)
        return list(self.db.scalars(stmt).all())

    def get_model_by_id(self, model_id: int) -> Optional[Model]:
        return self.db.get(Model, model_id)

    def get_active_model(self) -> Optional[Model]:
        stmt = select(Model).where(Model.status == "ACTIVE").order_by(Model.id.desc())
        return self.db.scalars(stmt).first()

    def save_model(self, model: Model) -> Model:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    # Datasets
    def list_datasets(self) -> List[Dataset]:
        stmt = select(Dataset)
        return list(self.db.scalars(stmt).all())

    def get_dataset_by_id(self, dataset_id: int) -> Optional[Dataset]:
        return self.db.get(Dataset, dataset_id)

    def save_dataset(self, dataset: Dataset) -> Dataset:
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    # Training Runs
    def list_training_runs(self) -> List[TrainingRun]:
        stmt = select(TrainingRun).order_by(TrainingRun.id.desc())
        return list(self.db.scalars(stmt).all())

    def get_training_run(self, run_id: int) -> Optional[TrainingRun]:
        stmt = (
            select(TrainingRun)
            .where(TrainingRun.id == run_id)
            .options(selectinload(TrainingRun.metrics))
        )
        return self.db.scalars(stmt).first()

    def save_training_run(self, run: TrainingRun) -> TrainingRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def add_training_metrics(self, metrics: List[TrainingMetric]) -> List[TrainingMetric]:
        self.db.add_all(metrics)
        self.db.commit()
        return metrics
