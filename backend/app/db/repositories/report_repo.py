"""Report and settings repository."""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.report import AppSetting, Report
from backend.app.db.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: Session):
        super().__init__(Report, db)

    def list_by_project(self, project_id: int) -> List[Report]:
        stmt = select(Report).where(Report.project_id == project_id)
        return list(self.db.scalars(stmt).all())

    def list_by_analysis(self, analysis_run_id: int) -> List[Report]:
        stmt = select(Report).where(Report.analysis_run_id == analysis_run_id)
        return list(self.db.scalars(stmt).all())


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str) -> Optional[Dict[str, Any]]:
        stmt = select(AppSetting).where(AppSetting.key == key)
        record = self.db.scalars(stmt).first()
        return record.value if record else None

    def set_setting(self, key: str, value: Dict[str, Any]) -> AppSetting:
        stmt = select(AppSetting).where(AppSetting.key == key)
        record = self.db.scalars(stmt).first()
        if record:
            record.value = value
        else:
            record = AppSetting(key=key, value=value)
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
