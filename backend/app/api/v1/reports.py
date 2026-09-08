"""Report generation and download endpoints."""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.job import ReportGenerateRequest, ReportResponse
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=List[ReportResponse])
def list_reports(
    project_id: Optional[int] = Query(None),
    analysis_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> List[ReportResponse]:
    service = ReportService(db)
    return service.list_reports(project_id=project_id, analysis_id=analysis_id)


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
) -> ReportResponse:
    service = ReportService(db)
    try:
        return service.generate_report(req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_GEN_ERROR", "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "REPORT_GEN_FAILED", "message": str(e)},
        )


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    report = service.get_report(report_id)
    if not report or not Path(report.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": f"Report with ID {report_id} not found on disk."},
        )

    media_type = "application/pdf" if report.report_type == "PDF" else "application/octet-stream"
    return FileResponse(
        path=report.file_path,
        filename=Path(report.file_path).name,
        media_type=media_type,
    )
