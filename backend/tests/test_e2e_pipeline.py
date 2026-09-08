"""End-to-End Pipeline and Database Integration Test."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_e2e_signal_analysis_pipeline(client: TestClient):
    """
    Validates complete end-to-end flow:
    Upload WAV signal -> Ingest & Save metadata in DB ->
    Trigger Analysis Pipeline -> Run DSP & Feature Extraction & AMC ->
    Persist AnalysisRun, AnalysisResult, Features, and Classification ->
    Generate Engineering PDF & JSON Reports -> Verify all DB records.
    """
    sample_wav = Path("samples/demo_qpsk.wav")
    assert sample_wav.exists(), "Sample demo_qpsk.wav must exist."

    # 1. Ingest Signal via API
    with open(sample_wav, "rb") as f:
        upload_resp = client.post(
            "/api/v1/signals/upload",
            files={"file": ("demo_qpsk.wav", f, "audio/wav")},
            data={"sample_rate": 100000.0, "center_frequency": 0.0},
        )
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    sig_info = upload_resp.json()
    signal_id = sig_info["id"]
    assert signal_id > 0
    assert sig_info["format"] == "WAV"
    assert sig_info["sample_rate"] == 1000000.0

    # 2. Trigger Complete Analysis Pipeline
    analysis_req = {
        "signal_id": signal_id,
        "mode": "full",
        "estimate_parameters": True,
        "extract_features": True,
        "classify": True,
        "synchronize": True,
        "demodulate": True,
        "decode": False,
        "target_modulation": "Auto",
        "confidence_threshold": 0.50,
    }
    run_resp = client.post("/api/v1/analysis", json=analysis_req)
    assert run_resp.status_code == 201, f"Analysis start failed: {run_resp.text}"
    run_data = run_resp.json()
    run_id = run_data["id"]
    assert run_id > 0
    assert run_data["status"] == "COMPLETED"

    # 3. Verify Calculated Results
    res = run_data["result"]
    assert res is not None
    assert res["carrier_frequency"] is not None
    assert res["occupied_bandwidth"] is not None
    assert res["snr"] is not None

    # 4. Verify Classification
    clf = run_data["classification"]
    assert clf is not None
    assert clf["predicted_class"] in ("QPSK", "BPSK", "8PSK", "16QAM", "FSK", "UNCERTAIN")
    assert clf["confidence"] > 0.0

    # 5. Verify Extracted Features in Database
    features = run_data["features"]
    assert len(features) > 10
    feature_names = {f["feature_name"] for f in features}
    assert "C21" in feature_names or "envelope_kurtosis" in feature_names

    # 6. Verify Processing History
    history = run_data["processing_history"]
    assert len(history) >= 4  # multiple pipeline stages recorded

    # 7. Generate Engineering PDF Report via Reports API
    rep_resp = client.post(
        "/api/v1/reports/generate",
        json={"analysis_id": run_id, "report_type": "PDF"},
    )
    assert rep_resp.status_code == 201, f"Report generation failed: {rep_resp.text}"
    rep_data = rep_resp.json()
    assert Path(rep_data["file_path"]).exists()

    # 8. Query Reports List
    list_reports = client.get(f"/api/v1/reports?analysis_id={run_id}")
    assert list_reports.status_code == 200
    assert len(list_reports.json()) >= 1
