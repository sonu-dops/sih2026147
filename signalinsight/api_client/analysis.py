"""Analysis API client module."""

from typing import Any, Dict, Optional
from signalinsight.api_client.base import BaseAPIClient


class AnalysisClient:
    def __init__(self, client: BaseAPIClient):
        self.client = client

    def start(
        self,
        signal_id: int,
        project_id: Optional[int] = None,
        mode: str = "full",
        estimate_parameters: bool = True,
        extract_features: bool = True,
        classify: bool = True,
        synchronize: bool = True,
        demodulate: bool = True,
        decode: bool = False,
        target_modulation: str = "Auto",
        confidence_threshold: float = 0.65,
    ) -> Dict[str, Any]:
        payload = {
            "signal_id": signal_id,
            "project_id": project_id,
            "mode": mode,
            "estimate_parameters": estimate_parameters,
            "extract_features": extract_features,
            "classify": classify,
            "synchronize": synchronize,
            "demodulate": demodulate,
            "decode": decode,
            "target_modulation": target_modulation,
            "confidence_threshold": confidence_threshold,
        }
        _, data = self.client.request("POST", "/api/v1/analysis", json_data=payload)
        return data

    def get(self, analysis_id: int) -> Dict[str, Any]:
        _, data = self.client.request("GET", f"/api/v1/analysis/{analysis_id}")
        return data

    def get_results(self, analysis_id: int) -> Dict[str, Any]:
        _, data = self.client.request("GET", f"/api/v1/analysis/{analysis_id}/results")
        return data

    def pause(self, analysis_id: int) -> Dict[str, Any]:
        _, data = self.client.request("POST", f"/api/v1/analysis/{analysis_id}/pause")
        return data

    def resume(self, analysis_id: int) -> Dict[str, Any]:
        _, data = self.client.request("POST", f"/api/v1/analysis/{analysis_id}/resume")
        return data

    def cancel(self, analysis_id: int) -> Dict[str, Any]:
        _, data = self.client.request("POST", f"/api/v1/analysis/{analysis_id}/cancel")
        return data
