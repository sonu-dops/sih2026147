"""Signal file ingestion, parsing, and storage service."""

from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models.signal import SignalFile, SignalMetadata
from backend.app.db.repositories.signal_repo import SignalRepository
from backend.app.schemas.signal import SignalDetailResponse, SignalFileResponse, SignalMetadataItem
from backend.app.storage.file_storage import FileStorageManager
from signalinsight.io.iq_loader import RawIQSignalLoader
from signalinsight.io.sigmf_loader import SigMFSignalLoader
from signalinsight.io.wav_loader import WavSignalLoader


class SignalService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SignalRepository(db)

    def list_signals(self, project_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[SignalFileResponse]:
        signals = self.repo.list_by_project(project_id=project_id, skip=skip, limit=limit)
        return [SignalFileResponse.model_validate(s) for s in signals]

    def get_signal(self, signal_id: int) -> Optional[SignalDetailResponse]:
        sig = self.repo.get_with_metadata(signal_id)
        if not sig:
            return None
        return SignalDetailResponse(
            id=sig.id,
            project_id=sig.project_id,
            filename=sig.filename,
            original_path=sig.original_path,
            file_hash=sig.file_hash,
            file_size=sig.file_size,
            format=sig.format,
            data_type=sig.data_type,
            iq_order=sig.iq_order,
            sample_count=sig.sample_count,
            sample_rate=sig.sample_rate,
            center_frequency=sig.center_frequency,
            duration=sig.duration,
            created_at=sig.created_at,
            metadata_records=[
                SignalMetadataItem(
                    parameter_name=m.parameter_name,
                    parameter_value=m.parameter_value,
                    unit=m.unit,
                    source=m.source,
                    confidence=m.confidence,
                )
                for m in sig.metadata_records
            ],
        )

    def delete_signal(self, signal_id: int) -> bool:
        sig = self.repo.get_by_id(signal_id)
        if not sig:
            return False
        # Remove physical file if stored
        if sig.original_path and Path(sig.original_path).exists():
            try:
                Path(sig.original_path).unlink()
            except Exception:
                pass
        self.repo.delete(sig)
        return True

    def ingest_signal_file(
        self,
        filename: str,
        content: bytes,
        project_id: Optional[int] = None,
        sample_rate_hint: Optional[float] = None,
        center_frequency_hint: Optional[float] = None,
    ) -> SignalFileResponse:
        """Saves file to storage, extracts metadata via signalinsight.io loaders, and persists to DB."""
        target_path, file_hash, file_size = FileStorageManager.save_uploaded_signal(filename, content)
        return self._register_file(
            file_path=target_path,
            original_filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            project_id=project_id,
            sample_rate_hint=sample_rate_hint,
            center_frequency_hint=center_frequency_hint,
        )

    def register_local_signal(
        self,
        local_path: Path,
        project_id: Optional[int] = None,
    ) -> SignalFileResponse:
        """Registers a local file already on disk."""
        target_path, file_hash, file_size = FileStorageManager.save_local_file_reference(local_path)
        return self._register_file(
            file_path=target_path,
            original_filename=local_path.name,
            file_hash=file_hash,
            file_size=file_size,
            project_id=project_id,
        )

    def _register_file(
        self,
        file_path: Path,
        original_filename: str,
        file_hash: str,
        file_size: int,
        project_id: Optional[int] = None,
        sample_rate_hint: Optional[float] = None,
        center_frequency_hint: Optional[float] = None,
    ) -> SignalFileResponse:
        ext = file_path.suffix.lower()
        fmt = "IQ"
        sample_count = 0
        sample_rate = sample_rate_hint or 1_000_000.0
        center_freq = center_frequency_hint or 0.0
        data_type = "complex64"
        iq_order = "IQ"
        metadata_items: List[SignalMetadata] = []

        try:
            if ext == ".wav":
                fmt = "WAV"
                loader = WavSignalLoader()
                rec = loader.load(file_path)
                sample_count = rec.sample_count
                sample_rate = rec.sample_rate
                center_freq = rec.center_frequency
                data_type = rec.data_type
            elif ext in (".sigmf-meta", ".sigmf-data"):
                fmt = "SIGMF"
                loader = SigMFSignalLoader()
                rec = loader.load(file_path)
                sample_count = rec.sample_count
                sample_rate = rec.sample_rate
                center_freq = rec.center_frequency
                data_type = rec.data_type
            else:
                fmt = "IQ"
                loader = RawIQSignalLoader()
                rec = loader.load(
                    file_path,
                    sample_rate=sample_rate,
                    center_frequency=center_freq,
                    data_type=data_type,
                )
                sample_count = rec.sample_count

            # Extract metadata items
            for k, v in rec.metadata.items():
                src = rec.metadata_sources.get(k, "CALCULATED")
                src_val = src.value if hasattr(src, "value") else str(src)
                metadata_items.append(
                    SignalMetadata(
                        parameter_name=k,
                        parameter_value=str(v),
                        unit="",
                        source=src_val,
                        confidence=1.0,
                    )
                )
        except Exception:
            # Fallback estimation if custom binary
            sample_count = file_size // 8

        duration = (sample_count / sample_rate) if sample_rate > 0 else 0.0

        sig_record = SignalFile(
            project_id=project_id,
            filename=original_filename,
            original_path=str(file_path),
            file_hash=file_hash,
            file_size=file_size,
            format=fmt,
            data_type=data_type,
            iq_order=iq_order,
            sample_count=sample_count,
            sample_rate=sample_rate,
            center_frequency=center_freq,
            duration=duration,
        )
        created_sig = self.repo.create(sig_record)

        # Attach metadata
        for m in metadata_items:
            m.signal_file_id = created_sig.id
        if metadata_items:
            self.repo.add_metadata_batch(metadata_items)

        return SignalFileResponse.model_validate(created_sig)
