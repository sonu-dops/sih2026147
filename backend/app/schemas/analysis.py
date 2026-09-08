"""Analysis request and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalysisCreateRequest(BaseModel):
    signal_id: int = Field(..., description="ID of the ingested signal file")
    project_id: Optional[int] = Field(None, description="Optional associated project ID")
    mode: str = Field("full", description="Analysis pipeline mode ('full', 'fast', 'quick')")
    remove_dc: bool = True
    normalize_rms: bool = False
    estimate_parameters: bool = True
    extract_features: bool = True
    classify: bool = True
    synchronize: bool = True
    demodulate: bool = True
    decode: bool = False
    target_modulation: str = "Auto"
    confidence_threshold: float = 0.65
    fec_type: str = "None"


class FeatureItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature_name: str
    feature_value: float
    unit: str = ""
    feature_version: str = "1.0.0"
    validity: bool = True


class AnalysisResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    carrier_frequency: Optional[float] = None
    carrier_offset: Optional[float] = None
    symbol_rate: Optional[float] = None
    occupied_bandwidth: Optional[float] = None
    bandwidth_3db: Optional[float] = None
    snr: Optional[float] = None
    signal_power: Optional[float] = None
    noise_floor: Optional[float] = None
    dc_offset_i: Optional[float] = None
    dc_offset_q: Optional[float] = None
    estimation_method: Optional[str] = None
    confidence: float = 1.0
    quality: str = "HIGH"


class ClassificationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    predicted_class: str
    confidence: float
    class_probabilities: Optional[Dict[str, float]] = None
    model_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    warnings: Optional[List[str]] = None


class ProcessingHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage: str
    operation: str
    status: str
    message: Optional[str] = None
    duration_ms: float
    timestamp: datetime


class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: Optional[int] = None
    signal_file_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pipeline_version: str
    error_message: Optional[str] = None


class FullAnalysisDetailResponse(AnalysisRunResponse):
    result: Optional[AnalysisResultResponse] = None
    classification: Optional[ClassificationSummary] = None
    features: List[FeatureItem] = Field(default_factory=list)
    processing_history: List[ProcessingHistoryItem] = Field(default_factory=list)
