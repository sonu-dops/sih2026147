"""Analysis run and results repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.analysis import AnalysisResult, AnalysisRun, Feature
from backend.app.db.models.job import ProcessingHistory
from backend.app.db.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[AnalysisRun]):
    def __init__(self, db: Session):
        super().__init__(AnalysisRun, db)

    def get_full_analysis(self, analysis_id: int) -> Optional[AnalysisRun]:
        stmt = (
            select(AnalysisRun)
            .where(AnalysisRun.id == analysis_id)
            .options(
                selectinload(AnalysisRun.result),
                selectinload(AnalysisRun.features),
                selectinload(AnalysisRun.classification),
                selectinload(AnalysisRun.processing_jobs),
                selectinload(AnalysisRun.processing_history),
                selectinload(AnalysisRun.signal_file),
            )
        )
        return self.db.scalars(stmt).first()

    def list_by_signal(self, signal_file_id: int) -> List[AnalysisRun]:
        stmt = select(AnalysisRun).where(AnalysisRun.signal_file_id == signal_file_id)
        return list(self.db.scalars(stmt).all())

    def list_by_project(self, project_id: int) -> List[AnalysisRun]:
        stmt = select(AnalysisRun).where(AnalysisRun.project_id == project_id)
        return list(self.db.scalars(stmt).all())

    def save_result(self, result: AnalysisResult) -> AnalysisResult:
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def save_features_batch(self, features: List[Feature]) -> List[Feature]:
        self.db.add_all(features)
        self.db.commit()
        return features

    def add_processing_history(self, entry: ProcessingHistory) -> ProcessingHistory:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
