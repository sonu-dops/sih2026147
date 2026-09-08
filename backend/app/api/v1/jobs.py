"""Processing job status and live WebSocket progress streaming."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal, get_db
from backend.app.schemas.job import JobResponse
from backend.app.services.job_service import JobService

router = APIRouter(tags=["Jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
) -> JobResponse:
    service = JobService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job with ID {job_id} does not exist."},
        )
    return job


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: int):
    """Streams live job status updates over WebSocket until completion or disconnect."""
    await websocket.accept()
    try:
        last_progress = -1
        while True:
            # Poll DB in threadsafe short intervals
            with SessionLocal() as db:
                service = JobService(db)
                job = service.get_job(job_id)
                if not job:
                    await websocket.send_json({"error": "JOB_NOT_FOUND", "job_id": job_id})
                    break

                if job.progress != last_progress or job.status in ("COMPLETED", "FAILED", "CANCELLED"):
                    last_progress = job.progress
                    await websocket.send_json({
                        "job_id": job.id,
                        "status": job.status,
                        "progress": job.progress,
                        "current_stage": job.current_stage,
                        "error_message": job.error_message,
                    })

                if job.status in ("COMPLETED", "FAILED", "CANCELLED"):
                    break

            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
