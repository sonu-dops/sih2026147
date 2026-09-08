"""Job management service."""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.db.repositories.job_repo import JobRepository
from backend.app.schemas.job import JobResponse


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)

    def get_job(self, job_id: int) -> Optional[JobResponse]:
        job = self.repo.get_by_id(job_id)
        return JobResponse.model_validate(job) if job else None

    def list_active_jobs(self) -> List[JobResponse]:
        jobs = self.repo.list_active()
        return [JobResponse.model_validate(j) for j in jobs]
