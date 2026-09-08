"""Base HTTP API Client with retries, timeout handling, and typed error responses."""

import json
import time
from typing import Any, Dict, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request


class APIClientError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class BaseAPIClient:
    """Centralized HTTP client for SignalInsight backend APIs."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 30.0

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retries: int = 2,
    ) -> Tuple[int, Any]:
        """Executes HTTP request with exponential backoff retries on transient connection errors."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            query_str = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query_str}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "SignalInsight-Client/1.0.0",
        }
        data_bytes = None
        if json_data is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(json_data).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method.upper())

        last_err = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status_code = resp.status
                    body = resp.read().decode("utf-8")
                    parsed = json.loads(body) if body else None
                    return status_code, parsed
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_body)
                    err_detail = err_json.get("error", {})
                    raise APIClientError(
                        code=err_detail.get("code", f"HTTP_{e.code}"),
                        message=err_detail.get("message", e.reason),
                        status_code=e.code,
                        details=err_detail.get("details", {}),
                    )
                except (json.JSONDecodeError, AttributeError):
                    raise APIClientError(
                        code=f"HTTP_{e.code}",
                        message=e.reason or err_body,
                        status_code=e.code,
                    )
            except (urllib.error.URLError, TimeoutError) as e:
                last_err = e
                if attempt < retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue

        raise APIClientError(
            code="NETWORK_ERROR",
            message=f"Failed to connect to backend at {self.base_url}: {last_err}",
            status_code=503,
        )
