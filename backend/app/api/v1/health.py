"""Health and system diagnostics endpoints."""

from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.database import get_db
from backend.app.db.repositories.amc_repo import AMCRepository
from backend.app.db.repositories.job_repo import JobRepository
from backend.app.schemas.common import DetailedHealthResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Basic health check endpoint."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        version="1.0.0",
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
def get_detailed_health(db: Session = Depends(get_db)) -> DetailedHealthResponse:
    """Comprehensive diagnostics across database, storage, DSP, and ML registry."""
    # 1. Database
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    # 2. Filesystem
    try:
        settings.init_storage_dirs()
        fs_status = "accessible"
    except Exception as e:
        fs_status = f"inaccessible: {e}"

    # 3. DSP Engine
    try:
        import numpy as np
        from signalinsight.dsp.preprocessing import SignalPreprocessor
        dsp_status = "operational"
    except Exception as e:
        dsp_status = f"unavailable: {e}"

    # 4. ML Engine & Model Registry
    try:
        amc_repo = AMCRepository(db)
        active_model = amc_repo.get_active_model()
        ml_status = f"ready (active: {active_model.name if active_model else 'None'})"
        model_reg = "connected"
    except Exception as e:
        ml_status = f"error: {e}"
        model_reg = "error"

    # 5. Active Jobs
    job_repo = JobRepository(db)
    active_jobs = len(job_repo.list_active())

    overall_status = "healthy" if db_status == "connected" and fs_status == "accessible" else "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        database=db_status,
        version="1.0.0",
        filesystem=fs_status,
        dsp_engine=dsp_status,
        ml_engine=ml_status,
        model_registry=model_reg,
        active_jobs_count=active_jobs,
    )
