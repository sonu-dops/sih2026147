"""Jobs API client module."""

from typing import Any, Dict
from signalinsight.api_client.base import BaseAPIClient


class JobsClient:
    def __init__(self, client: BaseAPIClient):
        self.client = client

    def get(self, job_id: int) -> Dict[str, Any]:
        _, data = self.client.request("GET", f"/api/v1/jobs/{job_id}")
        return data
