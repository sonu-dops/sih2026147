"""AMC, Dataset, Model, and Training request and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DirectClassificationRequest(BaseModel):
    signal_id: int = Field(..., description="ID of the signal file to classify")
    model_id: Optional[int] = Field(None, description="Optional specific model ID")
    confidence_threshold: float = Field(0.65, ge=0.0, le=1.0)


class DirectClassificationResponse(BaseModel):
    predicted_modulation: str
    confidence: float
    class_probabilities: Dict[str, float]
    model_name: str
    model_version: str
    feature_version: str
    warnings: List[str] = Field(default_factory=list)


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    model_type: str
    version: str
    file_path: str
    feature_version: str
    classes: Optional[List[str]] = None
    status: str
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime


class DatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    num_samples_per_class: int = Field(50, ge=10, le=500)


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    source: str
    version: str
    sample_count: int
    feature_count: int
    classes: Optional[List[str]] = None
    created_at: datetime


class TrainingMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    epoch: int
    training_loss: Optional[float] = None
    validation_loss: Optional[float] = None
    training_accuracy: Optional[float] = None
    validation_accuracy: Optional[float] = None


class TrainingRunRequest(BaseModel):
    dataset_id: Optional[int] = None
    algorithm: str = "XGBoost"
    num_train_per_class: int = Field(100, ge=20, le=500)
    num_test_per_class: int = Field(30, ge=10, le=100)


class TrainingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: Optional[int] = None
    model_id: Optional[int] = None
    algorithm: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    training_accuracy: Optional[float] = None
    validation_accuracy: Optional[float] = None
    test_accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None


class TrainingRunDetailResponse(TrainingRunResponse):
    metrics: List[TrainingMetricResponse] = Field(default_factory=list)
