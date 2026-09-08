"""Analysis execution and results endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisResultResponse,
    FullAnalysisDetailResponse,
)
from backend.app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("", response_model=FullAnalysisDetailResponse, status_code=status.HTTP_201_CREATED)
def start_analysis(
    req: AnalysisCreateRequest,
    db: Session = Depends(get_db),
) -> FullAnalysisDetailResponse:
    service = AnalysisService(db)
    try:
        return service.create_and_run_analysis(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SIGNAL_NOT_FOUND", "message": str(e)},
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ANALYSIS_FAILED", "message": str(e)},
        )


@router.get("/{analysis_id}", response_model=FullAnalysisDetailResponse)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> FullAnalysisDetailResponse:
    service = AnalysisService(db)
    analysis = service.get_analysis_detail(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis run with ID {analysis_id} does not exist."},
        )
    return analysis


@router.get("/{analysis_id}/results", response_model=AnalysisResultResponse)
def get_analysis_results(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> AnalysisResultResponse:
    service = AnalysisService(db)
    analysis = service.get_analysis_detail(analysis_id)
    if not analysis or not analysis.result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESULTS_NOT_FOUND", "message": f"Results for analysis run {analysis_id} not available."},
        )
    return analysis.result


@router.post("/{analysis_id}/pause")
def pause_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    if not service.pause_analysis(analysis_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis run {analysis_id} not found."},
        )
    return {"status": "PAUSED", "analysis_id": analysis_id}


@router.post("/{analysis_id}/resume")
def resume_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    if not service.resume_analysis(analysis_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis run {analysis_id} not found."},
        )
    return {"status": "RUNNING", "analysis_id": analysis_id}


@router.post("/{analysis_id}/cancel")
def cancel_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    if not service.cancel_analysis(analysis_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis run {analysis_id} not found."},
        )
    return {"status": "CANCELLED", "analysis_id": analysis_id}
