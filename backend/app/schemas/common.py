"""Common API schemas and standardized error models."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable error description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context or validation details")


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "healthy"
    database: str = "connected"
    version: str = "1.0.0"


class DetailedHealthResponse(BaseModel):
    status: str
    database: str
    version: str
    filesystem: str
    dsp_engine: str
    ml_engine: str
    model_registry: str
    active_jobs_count: int
