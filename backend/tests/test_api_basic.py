"""Tests for Health, Project CRUD, and Signal ingestion APIs."""

import io
from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

    resp_det = client.get("/api/v1/health/detailed")
    assert resp_det.status_code == 200
    data_det = resp_det.json()
    assert data_det["filesystem"] == "accessible"
    assert data_det["dsp_engine"] == "operational"


def test_project_crud(client: TestClient):
    # 1. Create project
    create_resp = client.post(
        "/api/v1/projects",
        json={"name": "Integration Test Project", "description": "Testing CRUD flow"},
    )
    assert create_resp.status_code == 201
    proj = create_resp.json()
    proj_id = proj["id"]
    assert proj["name"] == "Integration Test Project"

    # 2. List projects
    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    assert any(p["id"] == proj_id for p in list_resp.json())

    # 3. Get single project
    get_resp = client.get(f"/api/v1/projects/{proj_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Integration Test Project"

    # 4. Update project
    update_resp = client.put(
        f"/api/v1/projects/{proj_id}",
        json={"description": "Updated Description"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated Description"

    # 5. Delete project
    del_resp = client.delete(f"/api/v1/projects/{proj_id}")
    assert del_resp.status_code == 204

    # 6. Verify 404 with standardized error format
    get_again = client.get(f"/api/v1/projects/{proj_id}")
    assert get_again.status_code == 404
    err = get_again.json()["error"]
    assert err["code"] == "PROJECT_NOT_FOUND"


def test_signal_upload_and_retrieve(client: TestClient):
    # Create sample byte content (mock binary IQ)
    dummy_bytes = b"\x00\x01\x02\x03" * 256
    file_payload = {"file": ("test_capture.iq", io.BytesIO(dummy_bytes), "application/octet-stream")}

    upload_resp = client.post(
        "/api/v1/signals/upload",
        files=file_payload,
        data={"sample_rate": 1000000.0, "center_frequency": 433000000.0},
    )
    assert upload_resp.status_code == 201
    sig_data = upload_resp.json()
    sig_id = sig_data["id"]
    assert sig_data["filename"] == "test_capture.iq"
    assert sig_data["sample_rate"] == 1000000.0

    # Retrieve details
    detail_resp = client.get(f"/api/v1/signals/{sig_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == sig_id

    # Clean up
    del_resp = client.delete(f"/api/v1/signals/{sig_id}")
    assert del_resp.status_code == 204
