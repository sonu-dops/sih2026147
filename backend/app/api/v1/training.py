"""Model training endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.amc import (
    TrainingMetricResponse,
    TrainingRunDetailResponse,
    TrainingRunRequest,
    TrainingRunResponse,
)
from backend.app.services.amc_service import AMCService

router = APIRouter(prefix="/training", tags=["Training"])


@router.post("", response_model=TrainingRunDetailResponse, status_code=status.HTTP_201_CREATED)
def start_training(
    req: TrainingRunRequest,
    db: Session = Depends(get_db),
) -> TrainingRunDetailResponse:
    service = AMCService(db)
    try:
        return service.run_training(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "TRAINING_FAILED", "message": str(e)},
        )


@router.get("", response_model=List[TrainingRunResponse])
def list_training_runs(
    db: Session = Depends(get_db),
) -> List[TrainingRunResponse]:
    service = AMCService(db)
    return service.list_training_runs()


@router.get("/{run_id}", response_model=TrainingRunDetailResponse)
def get_training_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> TrainingRunDetailResponse:
    service = AMCService(db)
    run = service.get_training_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TRAINING_RUN_NOT_FOUND", "message": f"Training run {run_id} does not exist."},
        )
    return run


@router.get("/{run_id}/metrics", response_model=List[TrainingMetricResponse])
def get_training_metrics(
    run_id: int,
    db: Session = Depends(get_db),
) -> List[TrainingMetricResponse]:
    service = AMCService(db)
    run = service.get_training_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TRAINING_RUN_NOT_FOUND", "message": f"Training run {run_id} does not exist."},
        )
    return run.metrics
