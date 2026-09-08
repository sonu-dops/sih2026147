"""Signals API client module."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import uuid

from signalinsight.api_client.base import BaseAPIClient


class SignalsClient:
    def __init__(self, client: BaseAPIClient):
        self.client = client

    def list(self, project_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"skip": skip, "limit": limit}
        if project_id is not None:
            params["project_id"] = project_id
        _, data = self.client.request("GET", "/api/v1/signals", params=params)
        return data or []

    def get(self, signal_id: int) -> Dict[str, Any]:
        _, data = self.client.request("GET", f"/api/v1/signals/{signal_id}")
        return data

    def delete(self, signal_id: int) -> None:
        self.client.request("DELETE", f"/api/v1/signals/{signal_id}")

    def upload_file(
        self,
        filepath: Path,
        project_id: Optional[int] = None,
        sample_rate: Optional[float] = None,
        center_frequency: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Uploads a local signal file using multipart/form-data."""
        filepath = Path(filepath)
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        crlf = "\r\n".encode("utf-8")

        parts = []
        # File field
        filename = filepath.name
        with open(filepath, "rb") as f:
            file_bytes = f.read()

        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8"))
        parts.append("Content-Type: application/octet-stream".encode("utf-8"))
        parts.append(b"")
        parts.append(file_bytes)

        # Optional metadata fields
        if project_id is not None:
            parts.append(f"--{boundary}".encode("utf-8"))
            parts.append('Content-Disposition: form-data; name="project_id"'.encode("utf-8"))
            parts.append(b"")
            parts.append(str(project_id).encode("utf-8"))

        if sample_rate is not None:
            parts.append(f"--{boundary}".encode("utf-8"))
            parts.append('Content-Disposition: form-data; name="sample_rate"'.encode("utf-8"))
            parts.append(b"")
            parts.append(str(sample_rate).encode("utf-8"))

        if center_frequency is not None:
            parts.append(f"--{boundary}".encode("utf-8"))
            parts.append('Content-Disposition: form-data; name="center_frequency"'.encode("utf-8"))
            parts.append(b"")
            parts.append(str(center_frequency).encode("utf-8"))

        parts.append(f"--{boundary}--".encode("utf-8"))
        parts.append(b"")

        body = crlf.join(parts)
        url = f"{self.client.base_url}/api/v1/signals/upload"
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "SignalInsight-Client/1.0.0",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60.0) as resp:
            import json
            return json.loads(resp.read().decode("utf-8"))
