"""Processing job repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.job import ProcessingJob
from backend.app.db.repositories.base import BaseRepository


class JobRepository(BaseRepository[ProcessingJob]):
    def __init__(self, db: Session):
        super().__init__(ProcessingJob, db)

    def get_by_analysis(self, analysis_run_id: int) -> Optional[ProcessingJob]:
        stmt = select(ProcessingJob).where(ProcessingJob.analysis_run_id == analysis_run_id)
        return self.db.scalars(stmt).first()

    def list_active(self) -> List[ProcessingJob]:
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.status.in_(["QUEUED", "RUNNING"]))
            .order_by(ProcessingJob.id.desc())
        )
        return list(self.db.scalars(stmt).all())
