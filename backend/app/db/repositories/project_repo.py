"""Project repository implementation."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.project import Project
from backend.app.db.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session):
        super().__init__(Project, db)

    def get_with_relations(self, project_id: int) -> Optional[Project]:
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.signal_files),
                selectinload(Project.analysis_runs),
                selectinload(Project.reports),
            )
        )
        return self.db.scalars(stmt).first()

    def get_by_name(self, name: str) -> Optional[Project]:
        stmt = select(Project).where(Project.name == name)
        return self.db.scalars(stmt).first()
