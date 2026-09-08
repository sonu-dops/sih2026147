"""Project management service."""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models.project import Project
from backend.app.db.repositories.project_repo import ProjectRepository
from backend.app.schemas.project import ProjectCreate, ProjectDetailResponse, ProjectResponse, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectRepository(db)

    def list_projects(self, skip: int = 0, limit: int = 100) -> List[ProjectResponse]:
        projects = self.repo.list_all(skip=skip, limit=limit)
        return [ProjectResponse.model_validate(p) for p in projects]

    def create_project(self, data: ProjectCreate) -> ProjectResponse:
        proj = Project(
            name=data.name,
            description=data.description,
            status="ACTIVE",
        )
        created = self.repo.create(proj)
        return ProjectResponse.model_validate(created)

    def get_project(self, project_id: int) -> Optional[ProjectDetailResponse]:
        proj = self.repo.get_with_relations(project_id)
        if not proj:
            return None
        return ProjectDetailResponse(
            id=proj.id,
            name=proj.name,
            description=proj.description,
            status=proj.status,
            created_at=proj.created_at,
            updated_at=proj.updated_at,
            signal_files_count=len(proj.signal_files),
            analysis_runs_count=len(proj.analysis_runs),
            reports_count=len(proj.reports),
        )

    def update_project(self, project_id: int, data: ProjectUpdate) -> Optional[ProjectResponse]:
        proj = self.repo.get_by_id(project_id)
        if not proj:
            return None
        if data.name is not None:
            proj.name = data.name
        if data.description is not None:
            proj.description = data.description
        if data.status is not None:
            proj.status = data.status
        updated = self.repo.update(proj)
        return ProjectResponse.model_validate(updated)

    def delete_project(self, project_id: int) -> bool:
        proj = self.repo.get_by_id(project_id)
        if not proj:
            return False
        self.repo.delete(proj)
        return True
