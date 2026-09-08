"""Unit tests for SignalInsight Python API Client."""

from backend.app.schemas.project import ProjectCreate
from backend.app.services.project_service import ProjectService
from signalinsight.api_client import SignalInsightAPIClient
from signalinsight.api_client.base import APIClientError


def test_api_client_health(client):
    # Using client's base_url
    api = SignalInsightAPIClient(base_url="http://testserver")

    # Monkeypatch request to route through the fastapi testclient
    def mock_request(method, path, params=None, json_data=None, retries=0):
        url = path
        if params:
            import urllib.parse
            q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{q}"
        resp = client.request(method, url, json=json_data)
        if resp.status_code >= 400:
            err = resp.json().get("error", {})
            raise APIClientError(
                code=err.get("code", f"HTTP_{resp.status_code}"),
                message=err.get("message", "Error"),
                status_code=resp.status_code,
            )
        return resp.status_code, resp.json()

    api.request = mock_request

    # Test health
    health = api.health()
    assert health["status"] == "healthy"
    assert health["database"] == "connected"

    # Test projects client
    created = api.projects.create(name="Client Created Project", description="Via Python API Client")
    assert created["id"] > 0
    assert created["name"] == "Client Created Project"

    # Test projects list
    all_projects = api.projects.list()
    assert any(p["name"] == "Client Created Project" for p in all_projects)
