"""Report generation and export service."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.models.report import Report
from backend.app.db.repositories.analysis_repo import AnalysisRepository
from backend.app.db.repositories.report_repo import ReportRepository
from backend.app.schemas.job import ReportGenerateRequest, ReportResponse
from signalinsight.core.models import (
    AnalysisResult,
    ModulationResult,
    ParameterValue,
    ProvenanceSource,
    QualityLevel,
)
from signalinsight.reporting.csv_export import CSVExporter
from signalinsight.reporting.json_export import JSONExporter
from signalinsight.reporting.pdf_report import PDFReportGenerator


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.report_repo = ReportRepository(db)
        self.analysis_repo = AnalysisRepository(db)

    def list_reports(self, project_id: Optional[int] = None, analysis_id: Optional[int] = None) -> List[ReportResponse]:
        if project_id is not None:
            reports = self.report_repo.list_by_project(project_id)
        elif analysis_id is not None:
            reports = self.report_repo.list_by_analysis(analysis_id)
        else:
            reports = self.report_repo.list_all()
        return [ReportResponse.model_validate(r) for r in reports]

    def get_report(self, report_id: int) -> Optional[Report]:
        return self.report_repo.get_by_id(report_id)

    def generate_report(self, req: ReportGenerateRequest) -> ReportResponse:
        settings.init_storage_dirs()
        run = self.analysis_repo.get_full_analysis(req.analysis_id)
        if not run or not run.result:
            raise ValueError(f"Completed analysis with ID {req.analysis_id} not found.")

        # Reconstruct domain AnalysisResult for the exporters
        mod_result = None
        if run.classification:
            mod_result = ModulationResult(
                predicted_modulation=run.classification.predicted_class,
                confidence=run.classification.confidence,
                class_probabilities=run.classification.class_probabilities or {},
                model_version=run.classification.model_version,
                feature_version=run.classification.feature_version,
                warnings=run.classification.warnings or [],
            )

        features_dict = {
            f.feature_name: ParameterValue(
                name=f.feature_name,
                value=f.feature_value,
                unit=f.unit,
                source=ProvenanceSource.CALCULATED,
                confidence=1.0,
                quality=QualityLevel.HIGH,
            )
            for f in run.features
        }

        domain_result = AnalysisResult(
            session_id=f"analysis_{run.id}",
            timestamp=run.completed_at or datetime.utcnow(),
            source_file=run.signal_file.filename if run.signal_file else "N/A",
            file_hash_sha256=run.signal_file.file_hash if run.signal_file else "N/A",
            sample_rate=ParameterValue(
                name="Sample Rate",
                value=run.signal_file.sample_rate if run.signal_file else 0.0,
                unit="Hz",
                source=ProvenanceSource.MEASURED,
            ),
            carrier_frequency=ParameterValue(
                name="Carrier Frequency",
                value=run.result.carrier_frequency,
                unit="Hz",
                source=ProvenanceSource.ESTIMATED,
            ),
            carrier_offset=ParameterValue(
                name="Carrier Offset",
                value=run.result.carrier_offset,
                unit="Hz",
                source=ProvenanceSource.ESTIMATED,
            ),
            occupied_bw_99=ParameterValue(
                name="99% OBW",
                value=run.result.occupied_bandwidth,
                unit="Hz",
                source=ProvenanceSource.CALCULATED,
            ),
            bandwidth_3db=ParameterValue(
                name="3 dB Bandwidth",
                value=run.result.bandwidth_3db,
                unit="Hz",
                source=ProvenanceSource.CALCULATED,
            ),
            symbol_rate=ParameterValue(
                name="Symbol Rate",
                value=run.result.symbol_rate,
                unit="Baud",
                source=ProvenanceSource.ESTIMATED,
            ),
            snr_db=ParameterValue(
                name="SNR",
                value=run.result.snr,
                unit="dB",
                source=ProvenanceSource.ESTIMATED,
            ),
            signal_power=ParameterValue(
                name="Signal Power",
                value=run.result.signal_power,
                unit="dBFS",
                source=ProvenanceSource.CALCULATED,
            ),
            noise_floor=ParameterValue(
                name="Noise Floor",
                value=run.result.noise_floor,
                unit="dBFS/Hz",
                source=ProvenanceSource.ESTIMATED,
            ),
            features=features_dict,
            modulation_result=mod_result,
        )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rtype = req.report_type.upper()

        if rtype == "PDF":
            target_file = settings.report_storage_path / f"report_run_{run.id}_{timestamp}.pdf"
            PDFReportGenerator.generate(domain_result, target_file)
        elif rtype == "JSON":
            target_file = settings.report_storage_path / f"results_run_{run.id}_{timestamp}.json"
            JSONExporter.export(domain_result, target_file)
        elif rtype == "CSV":
            target_file = settings.report_storage_path / f"metrics_run_{run.id}_{timestamp}.csv"
            CSVExporter.export(domain_result, target_file)
        else:
            raise ValueError(f"Unsupported report type: {rtype}")

        db_report = Report(
            project_id=run.project_id,
            analysis_run_id=run.id,
            report_type=rtype,
            file_path=str(target_file),
        )
        saved_report = self.report_repo.create(db_report)
        return ReportResponse.model_validate(saved_report)
