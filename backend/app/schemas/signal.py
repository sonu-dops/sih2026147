"""Signal file request and response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SignalMetadataItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parameter_name: str
    parameter_value: str
    unit: str = ""
    source: str = "CALCULATED"
    confidence: float = 1.0


class SignalFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: Optional[int] = None
    filename: str
    original_path: Optional[str] = None
    file_hash: str
    file_size: int
    format: str
    data_type: str
    iq_order: str
    sample_count: int
    sample_rate: float
    center_frequency: float
    duration: float
    created_at: datetime


class SignalDetailResponse(SignalFileResponse):
    metadata_records: List[SignalMetadataItem] = Field(default_factory=list)
