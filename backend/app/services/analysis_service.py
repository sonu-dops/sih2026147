"""Analysis service executing real DSP/ML pipelines and persisting all metrics."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models.analysis import AnalysisResult, AnalysisRun, Feature
from backend.app.db.models.amc import Classification
from backend.app.db.models.job import ProcessingHistory, ProcessingJob
from backend.app.db.repositories.analysis_repo import AnalysisRepository
from backend.app.db.repositories.job_repo import JobRepository
from backend.app.db.repositories.signal_repo import SignalRepository
from backend.app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisResultResponse,
    AnalysisRunResponse,
    ClassificationSummary,
    FeatureItem,
    FullAnalysisDetailResponse,
    ProcessingHistoryItem,
)
from signalinsight.io.iq_loader import RawIQSignalLoader
from signalinsight.io.sigmf_loader import SigMFSignalLoader
from signalinsight.io.wav_loader import WavSignalLoader
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.analysis_repo = AnalysisRepository(db)
        self.signal_repo = SignalRepository(db)
        self.job_repo = JobRepository(db)

    def create_and_run_analysis(self, req: AnalysisCreateRequest) -> FullAnalysisDetailResponse:
        signal_file = self.signal_repo.get_by_id(req.signal_id)
        if not signal_file:
            raise ValueError(f"Signal file with ID {req.signal_id} not found.")

        # 1. Create AnalysisRun
        run = AnalysisRun(
            project_id=req.project_id or signal_file.project_id,
            signal_file_id=signal_file.id,
            status="RUNNING",
            started_at=datetime.utcnow(),
            pipeline_version="1.0.0",
            configuration=req.model_dump(),
        )
        run = self.analysis_repo.create(run)

        # 2. Create ProcessingJob
        job = ProcessingJob(
            project_id=run.project_id,
            analysis_run_id=run.id,
            job_type="DSP_ANALYSIS",
            status="RUNNING",
            progress=0,
            current_stage="INITIALIZING",
            started_at=datetime.utcnow(),
        )
        job = self.job_repo.create(job)

        # 3. Load Signal Record
        file_path = Path(signal_file.original_path) if signal_file.original_path else None
        if not file_path or not file_path.exists():
            run.status = "FAILED"
            run.error_message = f"Physical file not found: {file_path}"
            job.status = "FAILED"
            job.error_message = run.error_message
            self.db.commit()
            raise FileNotFoundError(run.error_message)

        ext = file_path.suffix.lower()
        if ext == ".wav":
            loader = WavSignalLoader()
            rec = loader.load(file_path)
        elif ext in (".sigmf-meta", ".sigmf-data"):
            loader = SigMFSignalLoader()
            rec = loader.load(file_path)
        else:
            loader = RawIQSignalLoader()
            rec = loader.load(
                file_path,
                sample_rate=signal_file.sample_rate or 1_000_000.0,
                center_frequency=signal_file.center_frequency or 0.0,
                data_type=signal_file.data_type or "complex64",
            )

        # 4. Configure Pipeline Options
        opts = PipelineOptions(
            remove_dc=req.remove_dc,
            normalize_rms=req.normalize_rms,
            estimate_parameters=req.estimate_parameters,
            extract_features=req.extract_features,
            run_amc=req.classify,
            run_sync=req.synchronize,
            run_demod=req.demodulate,
            run_decode=req.decode,
            target_modulation=req.target_modulation,
            confidence_threshold=req.confidence_threshold,
            fec_type=req.fec_type,
        )

        def progress_cb(pct: int, msg: str):
            job.progress = pct
            job.current_stage = msg
            self.db.commit()

        # 5. Execute DSP & ML Pipeline
        runner = PipelineRunner()
        try:
            result = runner.run(rec, options=opts, progress_callback=progress_cb)
        except Exception as e:
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            job.status = "FAILED"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise RuntimeError(f"Pipeline execution failed: {e}")

        # 6. Save Analysis Result
        db_result = AnalysisResult(
            analysis_run_id=run.id,
            carrier_frequency=result.carrier_frequency.value,
            carrier_offset=result.carrier_offset.value,
            symbol_rate=result.symbol_rate.value,
            occupied_bandwidth=result.occupied_bw_99.value,
            bandwidth_3db=result.bandwidth_3db.value,
            snr=result.snr_db.value,
            signal_power=result.signal_power.value,
            noise_floor=result.noise_floor.value,
            dc_offset_i=result.dc_offset_i.value,
            dc_offset_q=result.dc_offset_q.value,
            estimation_method="SignalInsight DSP Estimators",
            confidence=1.0,
            quality="HIGH",
        )
        self.analysis_repo.save_result(db_result)

        # 7. Save Features
        feature_entries = []
        for feat_name, param_val in result.features.items():
            if param_val.value is not None and isinstance(param_val.value, (int, float)):
                feature_entries.append(
                    Feature(
                        analysis_run_id=run.id,
                        feature_name=feat_name,
                        feature_value=float(param_val.value),
                        unit=param_val.unit or "",
                        feature_version="1.0.0",
                        validity=True,
                    )
                )
        for cum_name, param_val in result.cumulants.items():
            if param_val.value is not None and isinstance(param_val.value, (int, float)):
                feature_entries.append(
                    Feature(
                        analysis_run_id=run.id,
                        feature_name=cum_name,
                        feature_value=float(param_val.value),
                        unit=param_val.unit or "",
                        feature_version="1.0.0",
                        validity=True,
                    )
                )
        if feature_entries:
            self.analysis_repo.save_features_batch(feature_entries)

        # 8. Save Classification
        if result.modulation_result:
            clf = Classification(
                analysis_run_id=run.id,
                predicted_class=result.modulation_result.predicted_modulation,
                confidence=result.modulation_result.confidence,
                class_probabilities=result.modulation_result.class_probabilities,
                model_version=result.modulation_result.model_version,
                feature_version=result.modulation_result.feature_version,
                warnings=result.modulation_result.warnings,
            )
            self.db.add(clf)

        # 9. Save Processing History
        for stage_name, duration_ms in result.processing_times_ms.items():
            hist = ProcessingHistory(
                project_id=run.project_id,
                analysis_run_id=run.id,
                stage="PIPELINE",
                operation=stage_name,
                status="COMPLETED",
                message=f"Completed {stage_name} in {duration_ms:.2f} ms",
                duration_ms=duration_ms,
            )
            self.analysis_repo.add_processing_history(hist)

        # 10. Update Run and Job Status to COMPLETED
        now = datetime.utcnow()
        run.status = "COMPLETED"
        run.completed_at = now
        job.status = "COMPLETED"
        job.progress = 100
        job.current_stage = "COMPLETED"
        job.completed_at = now
        self.db.commit()

        return self.get_analysis_detail(run.id)  # type: ignore

    def get_analysis_detail(self, run_id: int) -> Optional[FullAnalysisDetailResponse]:
        run = self.analysis_repo.get_full_analysis(run_id)
        if not run:
            return None

        result_dto = None
        if run.result:
            result_dto = AnalysisResultResponse(
                carrier_frequency=run.result.carrier_frequency,
                carrier_offset=run.result.carrier_offset,
                symbol_rate=run.result.symbol_rate,
                occupied_bandwidth=run.result.occupied_bandwidth,
                bandwidth_3db=run.result.bandwidth_3db,
                snr=run.result.snr,
                signal_power=run.result.signal_power,
                noise_floor=run.result.noise_floor,
                dc_offset_i=run.result.dc_offset_i,
                dc_offset_q=run.result.dc_offset_q,
                estimation_method=run.result.estimation_method,
                confidence=run.result.confidence,
                quality=run.result.quality,
            )

        clf_dto = None
        if run.classification:
            clf_dto = ClassificationSummary(
                predicted_class=run.classification.predicted_class,
                confidence=run.classification.confidence,
                class_probabilities=run.classification.class_probabilities,
                model_version=run.classification.model_version,
                feature_version=run.classification.feature_version,
                warnings=run.classification.warnings,
            )

        return FullAnalysisDetailResponse(
            id=run.id,
            project_id=run.project_id,
            signal_file_id=run.signal_file_id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            pipeline_version=run.pipeline_version,
            error_message=run.error_message,
            result=result_dto,
            classification=clf_dto,
            features=[
                FeatureItem(
                    feature_name=f.feature_name,
                    feature_value=f.feature_value,
                    unit=f.unit,
                    feature_version=f.feature_version,
                    validity=f.validity,
                )
                for f in run.features
            ],
            processing_history=[
                ProcessingHistoryItem(
                    stage=h.stage,
                    operation=h.operation,
                    status=h.status,
                    message=h.message,
                    duration_ms=h.duration_ms,
                    timestamp=h.timestamp,
                )
                for h in run.processing_history
            ],
        )

    def pause_analysis(self, run_id: int) -> bool:
        run = self.analysis_repo.get_by_id(run_id)
        if not run:
            return False
        run.status = "PAUSED"
        job = self.job_repo.get_by_analysis(run_id)
        if job:
            job.status = "PAUSED"
        self.db.commit()
        return True

    def resume_analysis(self, run_id: int) -> bool:
        run = self.analysis_repo.get_by_id(run_id)
        if not run:
            return False
        run.status = "RUNNING"
        job = self.job_repo.get_by_analysis(run_id)
        if job:
            job.status = "RUNNING"
        self.db.commit()
        return True

    def cancel_analysis(self, run_id: int) -> bool:
        run = self.analysis_repo.get_by_id(run_id)
        if not run:
            return False
        run.status = "CANCELLED"
        job = self.job_repo.get_by_analysis(run_id)
        if job:
            job.status = "CANCELLED"
        self.db.commit()
        return True
