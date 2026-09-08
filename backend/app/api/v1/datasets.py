"""Dataset management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.amc import DatasetCreateRequest, DatasetResponse
from backend.app.services.amc_service import AMCService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    req: DatasetCreateRequest,
    db: Session = Depends(get_db),
) -> DatasetResponse:
    service = AMCService(db)
    return service.create_synthetic_dataset(req)


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
) -> List[DatasetResponse]:
    service = AMCService(db)
    return service.list_datasets()


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
) -> DatasetResponse:
    service = AMCService(db)
    dataset = service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset with ID {dataset_id} does not exist."},
        )
    return dataset
