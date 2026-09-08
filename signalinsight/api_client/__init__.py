"""SignalInsight Centralized API Client."""

from typing import Any, Dict
from signalinsight.api_client.analysis import AnalysisClient
from signalinsight.api_client.base import APIClientError, BaseAPIClient
from signalinsight.api_client.jobs import JobsClient
from signalinsight.api_client.projects import ProjectsClient
from signalinsight.api_client.reports import ReportsClient
from signalinsight.api_client.signals import SignalsClient


class SignalInsightAPIClient(BaseAPIClient):
    """Unified API client providing access to all SignalInsight backend resources."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        super().__init__(base_url)
        self.projects = ProjectsClient(self)
        self.signals = SignalsClient(self)
        self.analysis = AnalysisClient(self)
        self.jobs = JobsClient(self)
        self.reports = ReportsClient(self)

    def health(self) -> Dict[str, Any]:
        _, data = self.request("GET", "/api/v1/health")
        return data

    def detailed_health(self) -> Dict[str, Any]:
        _, data = self.request("GET", "/api/v1/health/detailed")
        return data


__all__ = [
    "SignalInsightAPIClient",
    "BaseAPIClient",
    "APIClientError",
    "ProjectsClient",
    "SignalsClient",
    "AnalysisClient",
    "JobsClient",
    "ReportsClient",
]
