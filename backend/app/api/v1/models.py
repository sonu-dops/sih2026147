"""Model registry endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.amc import ModelResponse
from backend.app.services.amc_service import AMCService

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=List[ModelResponse])
def list_models(
    db: Session = Depends(get_db),
) -> List[ModelResponse]:
    service = AMCService(db)
    return service.list_models()


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
) -> ModelResponse:
    service = AMCService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MODEL_NOT_FOUND", "message": f"Model with ID {model_id} does not exist."},
        )
    return model


@router.post("/{model_id}/activate", response_model=ModelResponse)
def activate_model(
    model_id: int,
    db: Session = Depends(get_db),
) -> ModelResponse:
    service = AMCService(db)
    model = service.activate_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MODEL_NOT_FOUND", "message": f"Model with ID {model_id} does not exist."},
        )
    return model


@router.post("/{model_id}/deactivate", response_model=ModelResponse)
def deactivate_model(
    model_id: int,
    db: Session = Depends(get_db),
) -> ModelResponse:
    service = AMCService(db)
    model = service.deactivate_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MODEL_NOT_FOUND", "message": f"Model with ID {model_id} does not exist."},
        )
    return model
