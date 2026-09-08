"""Application settings endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.repositories.report_repo import SettingsRepository
from backend.app.schemas.job import SettingUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/{key}")
def get_setting(
    key: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    repo = SettingsRepository(db)
    val = repo.get_setting(key)
    if val is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SETTING_NOT_FOUND", "message": f"Setting '{key}' not found."},
        )
    return {"key": key, "value": val}


@router.put("/{key}")
def update_setting(
    key: str,
    update: SettingUpdate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    repo = SettingsRepository(db)
    record = repo.set_setting(key, update.value)
    return {"key": record.key, "value": record.value, "updated_at": record.updated_at}
