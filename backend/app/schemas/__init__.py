"""API schemas package."""

from backend.app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    DetailedHealthResponse,
)
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
)
from backend.app.schemas.signal import (
    SignalFileResponse,
    SignalDetailResponse,
    SignalMetadataItem,
)
from backend.app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisRunResponse,
    AnalysisResultResponse,
    FullAnalysisDetailResponse,
    FeatureItem,
    ClassificationSummary,
    ProcessingHistoryItem,
)
from backend.app.schemas.amc import (
    DirectClassificationRequest,
    DirectClassificationResponse,
    ModelResponse,
    DatasetCreateRequest,
    DatasetResponse,
    TrainingRunRequest,
    TrainingRunResponse,
    TrainingRunDetailResponse,
    TrainingMetricResponse,
)
from backend.app.schemas.job import (
    JobResponse,
    ReportGenerateRequest,
    ReportResponse,
    SettingUpdate,
)

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "DetailedHealthResponse",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectDetailResponse",
    "SignalFileResponse",
    "SignalDetailResponse",
    "SignalMetadataItem",
    "AnalysisCreateRequest",
    "AnalysisRunResponse",
    "AnalysisResultResponse",
    "FullAnalysisDetailResponse",
    "FeatureItem",
    "ClassificationSummary",
    "ProcessingHistoryItem",
    "DirectClassificationRequest",
    "DirectClassificationResponse",
    "ModelResponse",
    "DatasetCreateRequest",
    "DatasetResponse",
    "TrainingRunRequest",
    "TrainingRunResponse",
    "TrainingRunDetailResponse",
    "TrainingMetricResponse",
    "JobResponse",
    "ReportGenerateRequest",
    "ReportResponse",
    "SettingUpdate",
]
