"""Projects API client module."""

from typing import Any, Dict, List, Optional
from signalinsight.api_client.base import BaseAPIClient


class ProjectsClient:
    def __init__(self, client: BaseAPIClient):
        self.client = client

    def list(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        _, data = self.client.request("GET", "/api/v1/projects", params={"skip": skip, "limit": limit})
        return data or []

    def get(self, project_id: int) -> Dict[str, Any]:
        _, data = self.client.request("GET", f"/api/v1/projects/{project_id}")
        return data

    def create(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        _, data = self.client.request("POST", "/api/v1/projects", json_data={"name": name, "description": description})
        return data

    def update(self, project_id: int, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        _, data = self.client.request("PUT", f"/api/v1/projects/{project_id}", json_data=payload)
        return data

    def delete(self, project_id: int) -> None:
        self.client.request("DELETE", f"/api/v1/projects/{project_id}")
