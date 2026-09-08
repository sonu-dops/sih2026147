"""Tests for Datasets, Training, Models, Jobs, Reports, and Settings APIs."""

from fastapi.testclient import TestClient


def test_dataset_and_models(client: TestClient):
    # Create synthetic dataset
    ds_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Benchmark Dataset A", "num_samples_per_class": 15},
    )
    assert ds_resp.status_code == 201
    ds_data = ds_resp.json()
    assert ds_data["sample_count"] == 15 * 5  # 5 modulation classes

    # List datasets
    list_ds = client.get("/api/v1/datasets")
    assert list_ds.status_code == 200
    assert len(list_ds.json()) >= 1

    # List models
    models_resp = client.get("/api/v1/models")
    assert models_resp.status_code == 200


def test_settings_api(client: TestClient):
    # Set setting
    put_resp = client.put(
        "/api/v1/settings/ui_preferences",
        json={"value": {"theme": "light_workstation", "default_fft_size": 4096}},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["value"]["default_fft_size"] == 4096

    # Get setting
    get_resp = client.get("/api/v1/settings/ui_preferences")
    assert get_resp.status_code == 200
    assert get_resp.json()["value"]["theme"] == "light_workstation"


def test_training_run_flow(client: TestClient):
    # Run short training
    train_resp = client.post(
        "/api/v1/training",
        json={"num_train_per_class": 25, "num_test_per_class": 10},
    )
    assert train_resp.status_code == 201
    run_data = train_resp.json()
    run_id = run_data["id"]
    assert run_data["status"] == "COMPLETED"
    assert run_data["training_accuracy"] is not None
    assert len(run_data["metrics"]) == 10  # 10 epoch records

    # Query metrics endpoint directly
    metrics_resp = client.get(f"/api/v1/training/{run_id}/metrics")
    assert metrics_resp.status_code == 200
    assert len(metrics_resp.json()) == 10
