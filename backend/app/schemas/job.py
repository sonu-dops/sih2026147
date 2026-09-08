"""Job, Report, and Settings Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: Optional[int] = None
    analysis_run_id: Optional[int] = None
    job_type: str
    status: str
    progress: int
    current_stage: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    analysis_id: int = Field(..., description="ID of the analysis run")
    report_type: str = Field("PDF", description="Type of report to generate (PDF, JSON, CSV, SIGMF)")


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: Optional[int] = None
    analysis_run_id: Optional[int] = None
    report_type: str
    file_path: str
    created_at: datetime


class SettingUpdate(BaseModel):
    value: Dict[str, Any]
