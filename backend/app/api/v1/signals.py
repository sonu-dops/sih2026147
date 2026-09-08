"""Signal ingestion and metadata management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.signal import SignalDetailResponse, SignalFileResponse
from backend.app.services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.post("/upload", response_model=SignalFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_signal(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    sample_rate: Optional[float] = Form(None),
    center_frequency: Optional[float] = Form(None),
    db: Session = Depends(get_db),
) -> SignalFileResponse:
    service = SignalService(db)
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "The uploaded file is empty."},
        )

    try:
        return service.ingest_signal_file(
            filename=file.filename or "uploaded_signal.bin",
            content=content,
            project_id=project_id,
            sample_rate_hint=sample_rate,
            center_frequency_hint=center_frequency,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "SIGNAL_INGESTION_ERROR", "message": str(e)},
        )


@router.get("", response_model=List[SignalFileResponse])
def list_signals(
    project_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[SignalFileResponse]:
    service = SignalService(db)
    return service.list_signals(project_id=project_id, skip=skip, limit=limit)


@router.get("/{signal_id}", response_model=SignalDetailResponse)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
) -> SignalDetailResponse:
    service = SignalService(db)
    sig = service.get_signal(signal_id)
    if not sig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SIGNAL_NOT_FOUND", "message": f"Signal with ID {signal_id} does not exist."},
        )
    return sig


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signal(
    signal_id: int,
    db: Session = Depends(get_db),
) -> None:
    service = SignalService(db)
    success = service.delete_signal(signal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SIGNAL_NOT_FOUND", "message": f"Signal with ID {signal_id} does not exist."},
        )
