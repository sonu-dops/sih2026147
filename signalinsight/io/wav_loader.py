"""WAV file loader for audio, baseband, and IQ stereo recordings."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from scipy.io import wavfile

from signalinsight.core.exceptions import UnsupportedFormatError
from signalinsight.core.models import ProvenanceSource, SignalRecord
from signalinsight.io.base import SignalLoader
from signalinsight.io.validator import SignalValidator


class WavSignalLoader(SignalLoader):
    """Loads mono real-valued and stereo IQ signals from standard WAV files."""

    def can_load(self, filepath: Path) -> bool:
        return filepath.suffix.lower() == ".wav"

    def inspect_metadata(self, filepath: Path) -> Dict[str, Any]:
        SignalValidator.validate_file(filepath)
        try:
            # Quick header read via scipy
            fs, data = wavfile.read(filepath, mmap=True)
            channels = 1 if data.ndim == 1 else data.shape[1]
            sample_count = data.shape[0]
            duration = sample_count / fs if fs > 0 else 0.0

            return {
                "file_name": filepath.name,
                "file_size": filepath.stat().st_size,
                "format": "WAV",
                "sample_rate": float(fs),
                "channels": channels,
                "sample_count": sample_count,
                "duration": duration,
                "data_type": str(data.dtype),
                "is_complex": channels == 2,
            }
        except Exception as e:
            raise UnsupportedFormatError(
                f"Failed to parse WAV header for {filepath.name}",
                technical_details=str(e),
                suggested_action="Ensure the WAV file has a valid standard RIFF/WAVE header.",
            )

    def load(
        self,
        filepath: Path,
        sample_rate: Optional[float] = None,
        center_frequency: Optional[float] = None,
        max_samples: Optional[int] = None,
        offset_samples: int = 0,
        **kwargs: Any,
    ) -> SignalRecord:
        SignalValidator.validate_file(filepath)
        fs, data = wavfile.read(filepath, mmap=True)

        if offset_samples > 0:
            data = data[offset_samples:]
        if max_samples is not None and max_samples > 0:
            data = data[:max_samples]

        # Convert to numpy array in memory
        raw_samples = np.asarray(data)

        # Normalize to float32 [-1.0, 1.0] if integer type
        if np.issubdtype(raw_samples.dtype, np.integer):
            info = np.iinfo(raw_samples.dtype)
            samples_float = raw_samples.astype(np.float32) / max(abs(info.min), abs(info.max))
        else:
            samples_float = raw_samples.astype(np.float32)

        metadata_sources: Dict[str, ProvenanceSource] = {}
        # Sample rate from WAV header is [USER] or file header
        effective_fs = float(sample_rate) if sample_rate is not None else float(fs)
        metadata_sources["sample_rate"] = ProvenanceSource.USER if sample_rate is not None else ProvenanceSource.MEASURED

        effective_fc = float(center_frequency) if center_frequency is not None else 0.0
        metadata_sources["center_frequency"] = ProvenanceSource.USER if center_frequency is not None else ProvenanceSource.MEASURED

        # Check channels
        if samples_float.ndim == 2 and samples_float.shape[1] >= 2:
            # Channel 0 = I, Channel 1 = Q
            complex_samples = samples_float[:, 0] + 1j * samples_float[:, 1]
            channels = 2
            iq_order = "IQ"
        else:
            # Mono real
            complex_samples = samples_float.flatten()
            channels = 1
            iq_order = "Real"

        SignalValidator.validate_samples(complex_samples, allow_real=True)

        meta = {
            "wav_header_fs": float(fs),
            "original_dtype": str(data.dtype),
            "channels": channels,
        }

        return SignalRecord(
            samples=complex_samples,
            sample_rate=effective_fs,
            center_frequency=effective_fc,
            timestamp=datetime.fromtimestamp(filepath.stat().st_mtime),
            source_file=filepath,
            data_type=str(data.dtype),
            channels=channels,
            iq_order=iq_order,
            metadata=meta,
            metadata_sources=metadata_sources,
        )
