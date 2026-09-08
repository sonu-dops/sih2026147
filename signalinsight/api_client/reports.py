"""Reports API client module."""

from typing import Any, Dict, List, Optional
from signalinsight.api_client.base import BaseAPIClient


class ReportsClient:
    def __init__(self, client: BaseAPIClient):
        self.client = client

    def list(self, project_id: Optional[int] = None, analysis_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if project_id is not None:
            params["project_id"] = project_id
        if analysis_id is not None:
            params["analysis_id"] = analysis_id
        _, data = self.client.request("GET", "/api/v1/reports", params=params)
        return data or []

    def generate(self, analysis_id: int, report_type: str = "PDF") -> Dict[str, Any]:
        _, data = self.client.request(
            "POST",
            "/api/v1/reports/generate",
            json_data={"analysis_id": analysis_id, "report_type": report_type},
        )
        return data
