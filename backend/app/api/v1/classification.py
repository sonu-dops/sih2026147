"""Direct Automatic Modulation Classification endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.amc import DirectClassificationRequest, DirectClassificationResponse
from backend.app.services.amc_service import AMCService

router = APIRouter(prefix="/classification", tags=["Classification"])


@router.post("", response_model=DirectClassificationResponse)
def classify_signal(
    req: DirectClassificationRequest,
    db: Session = Depends(get_db),
) -> DirectClassificationResponse:
    service = AMCService(db)
    try:
        return service.direct_classify(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SIGNAL_NOT_FOUND", "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CLASSIFICATION_FAILED", "message": str(e)},
        )
