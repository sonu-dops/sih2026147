"""Unit tests for pipeline runner and report generators (JSON, CSV, SigMF, PDF)."""

from pathlib import Path
import pytest

from signalinsight.amc.synthetic import SyntheticSignalGenerator
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner
from signalinsight.reporting.csv_export import CSVExporter
from signalinsight.reporting.json_export import JSONExporter
from signalinsight.reporting.pdf_report import PDFReportGenerator
from signalinsight.reporting.sigmf_export import SigMFExporter


def test_full_pipeline_qpsk(tmp_path: Path):
    rec = SyntheticSignalGenerator.generate(
        modulation="QPSK",
        sample_rate=1e6,
        symbol_rate=100e3,
        num_symbols=1200,
        snr_db=25.0,
        carrier_offset_hz=5000.0,
        seed=42,
    )

    runner = PipelineRunner()
    opts = PipelineOptions(run_amc=True, run_sync=True, run_demod=True, run_decode=False)

    progress_events = []

    def on_progress(pct, msg):
        progress_events.append((pct, msg))

    result = runner.run(rec, options=opts, progress_callback=on_progress)

    assert len(progress_events) > 0
    assert result.sample_rate.value == 1e6
    assert result.duration_s > 0
    assert result.snr_db.value is not None
    assert result.occupied_bw_99.value is not None
    assert result.modulation_result is not None
    assert result.demodulation_result is not None
    assert result.decoding_result is not None
    assert not result.decoding_result.available

    # JSON export test
    json_path = tmp_path / "analysis.json"
    JSONExporter.export(result, json_path)
    assert json_path.exists()
    assert json_path.stat().st_size > 500

    # CSV export test
    csv_path = tmp_path / "analysis.csv"
    CSVExporter.export(result, csv_path)
    assert csv_path.exists()
    assert csv_path.stat().st_size > 200

    # SigMF export test
    sigmf_path = tmp_path / "signal.sigmf-meta"
    SigMFExporter.export_metadata(rec, sigmf_path, analysis_result=result)
    assert sigmf_path.exists()
    assert sigmf_path.stat().st_size > 100

    # PDF report generation test
    pdf_path = tmp_path / "technical_report.pdf"
    PDFReportGenerator.generate(result, pdf_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000
