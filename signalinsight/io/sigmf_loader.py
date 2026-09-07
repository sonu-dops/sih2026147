"""SigMF (Signal Metadata Format) loader and parser."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np

from signalinsight.core.exceptions import FileValidationError, UnsupportedFormatError
from signalinsight.core.models import ProvenanceSource, SignalRecord
from signalinsight.io.base import SignalLoader
from signalinsight.io.validator import SignalValidator

SIGMF_DTYPE_MAP = {
    "cf32_le": ("<f4", "complex"),
    "cf32_be": (">f4", "complex"),
    "cf64_le": ("<f8", "complex"),
    "cf64_be": (">f8", "complex"),
    "ci16_le": ("<i2", "complex"),
    "ci16_be": (">i2", "complex"),
    "cu8": ("u1", "complex"),
    "ci8": ("i1", "complex"),
    "rf32_le": ("<f4", "real"),
    "ri16_le": ("<i2", "real"),
}


class SigMFSignalLoader(SignalLoader):
    """Loads recordings adhering to the SigMF specification."""

    def can_load(self, filepath: Path) -> bool:
        ext = filepath.suffix.lower()
        if ext == ".sigmf-meta":
            return True
        if ext == ".sigmf-data":
            meta_path = filepath.with_suffix(".sigmf-meta")
            return meta_path.exists()
        return False

    def _resolve_paths(self, filepath: Path) -> Tuple[Path, Path]:
        if filepath.suffix.lower() == ".sigmf-meta":
            meta_path = filepath
            data_path = filepath.with_name(filepath.stem + ".sigmf-data")
        else:
            data_path = filepath
            meta_path = filepath.with_name(filepath.stem + ".sigmf-meta")

        if not meta_path.exists():
            raise FileValidationError(f"SigMF metadata file missing: {meta_path.name}")
        if not data_path.exists():
            raise FileValidationError(f"SigMF dataset file missing: {data_path.name}")

        return meta_path, data_path

    def inspect_metadata(self, filepath: Path) -> Dict[str, Any]:
        meta_path, data_path = self._resolve_paths(filepath)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        global_meta = meta.get("global", {})
        captures = meta.get("captures", [{}])
        first_capture = captures[0] if captures else {}

        datatype = global_meta.get("core:datatype", "cf32_le")
        sample_rate = global_meta.get("core:sample_rate", 0.0)
        center_freq = first_capture.get("core:frequency", 0.0)
        dt_str = first_capture.get("core:datetime", None)

        file_size = data_path.stat().st_size
        np_dt_str, mode = SIGMF_DTYPE_MAP.get(datatype, ("<f4", "complex"))
        byte_size = np.dtype(np_dt_str).itemsize
        channels = 2 if mode == "complex" else 1
        total_samples = file_size // (byte_size * channels)

        return {
            "file_name": data_path.name,
            "format": "SigMF",
            "datatype": datatype,
            "sample_rate": float(sample_rate),
            "center_frequency": float(center_freq),
            "total_samples": total_samples,
            "duration": total_samples / sample_rate if sample_rate > 0 else 0.0,
            "datetime": dt_str,
            "description": global_meta.get("core:description", ""),
        }

    def load(
        self,
        filepath: Path,
        sample_rate: Optional[float] = None,
        center_frequency: Optional[float] = None,
        max_samples: Optional[int] = None,
        offset_samples: int = 0,
        **kwargs: Any,
    ) -> SignalRecord:
        meta_path, data_path = self._resolve_paths(filepath)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        global_meta = meta.get("global", {})
        captures = meta.get("captures", [{}])
        first_capture = captures[0] if captures else {}

        datatype = global_meta.get("core:datatype", "cf32_le")
        if datatype not in SIGMF_DTYPE_MAP:
            raise UnsupportedFormatError(f"Unsupported SigMF datatype: {datatype}")

        np_dt_str, mode = SIGMF_DTYPE_MAP[datatype]
        base_dtype = np.dtype(np_dt_str)
        is_complex = mode == "complex"
        channels = 2 if is_complex else 1

        sigmf_fs = global_meta.get("core:sample_rate", None)
        sigmf_fc = first_capture.get("core:frequency", 0.0)
        sigmf_time_str = first_capture.get("core:datetime", None)

        ts = datetime.utcnow()
        if sigmf_time_str:
            try:
                ts = datetime.fromisoformat(sigmf_time_str.replace("Z", "+00:00"))
            except Exception:
                pass

        meta_sources = {}
        if sample_rate is not None:
            effective_fs = float(sample_rate)
            meta_sources["sample_rate"] = ProvenanceSource.USER
        elif sigmf_fs is not None:
            effective_fs = float(sigmf_fs)
            meta_sources["sample_rate"] = ProvenanceSource.SIGMF
        else:
            raise FileValidationError("Sample rate not found in SigMF metadata or user arguments.")

        if center_frequency is not None:
            effective_fc = float(center_frequency)
            meta_sources["center_frequency"] = ProvenanceSource.USER
        else:
            effective_fc = float(sigmf_fc)
            meta_sources["center_frequency"] = ProvenanceSource.SIGMF

        # Read binary data
        offset_bytes = offset_samples * base_dtype.itemsize * channels
        values_to_read = max_samples * channels if max_samples else -1

        with open(data_path, "rb") as f:
            if offset_bytes > 0:
                f.seek(offset_bytes)
            raw_data = np.fromfile(f, dtype=base_dtype, count=values_to_read)

        # Normalize integers to float32
        if np.issubdtype(base_dtype, np.integer):
            info = np.iinfo(base_dtype)
            if np.issubdtype(base_dtype, np.unsignedinteger):
                center = (info.max + 1) / 2.0
                vals_float = (raw_data.astype(np.float32) - center) / center
            else:
                vals_float = raw_data.astype(np.float32) / float(max(abs(info.min), abs(info.max)))
        else:
            vals_float = raw_data.astype(np.float32)

        if is_complex:
            i_vals = vals_float[0::2]
            q_vals = vals_float[1::2]
            complex_samples = i_vals + 1j * q_vals
            iq_order = "IQ"
        else:
            complex_samples = vals_float
            iq_order = "Real"

        SignalValidator.validate_samples(complex_samples, allow_real=True)

        return SignalRecord(
            samples=complex_samples,
            sample_rate=effective_fs,
            center_frequency=effective_fc,
            timestamp=ts,
            source_file=data_path,
            data_type=datatype,
            channels=channels,
            iq_order=iq_order,
            metadata=meta,
            metadata_sources=meta_sources,
        )
