"""Raw IQ binary file loader with memory mapping and full format support."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

from signalinsight.core.exceptions import IncompleteMetadataError, UnsupportedFormatError
from signalinsight.core.models import ProvenanceSource, SignalRecord
from signalinsight.io.base import SignalLoader
from signalinsight.io.validator import SignalValidator

DTYPE_MAP = {
    "int8": np.int8,
    "uint8": np.uint8,
    "int16": np.int16,
    "uint16": np.uint16,
    "int32": np.int32,
    "float32": np.float32,
    "float64": np.float64,
}


class RawIQSignalLoader(SignalLoader):
    """
    Loads raw interleaved IQ binary recordings.
    Supports memory-mapping, arbitrary bit depths, endianness, and sample offsets.
    """

    SUPPORTED_EXTENSIONS = {".iq", ".raw", ".bin", ".dat", ".complex", ".fc32", ".sc16", ".u8"}

    def can_load(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def inspect_metadata(
        self,
        filepath: Path,
        data_type: str = "float32",
        channel_mode: str = "Complex",
        endianness: str = "Little Endian",
    ) -> Dict[str, Any]:
        SignalValidator.validate_file(filepath)
        file_size = filepath.stat().st_size

        dt_name = data_type.lower()
        if dt_name not in DTYPE_MAP:
            raise UnsupportedFormatError(f"Unsupported data type: {data_type}")

        base_dt = DTYPE_MAP[dt_name]
        byte_size = np.dtype(base_dt).itemsize
        channels = 2 if channel_mode.lower() == "complex" else 1

        total_values = file_size // byte_size
        total_samples = total_values // channels

        return {
            "file_name": filepath.name,
            "file_size": file_size,
            "format": "RAW_IQ",
            "data_type": data_type,
            "channel_mode": channel_mode,
            "endianness": endianness,
            "bytes_per_sample_component": byte_size,
            "total_samples": total_samples,
        }

    def load(
        self,
        filepath: Path,
        sample_rate: Optional[float] = None,
        center_frequency: Optional[float] = None,
        data_type: str = "float32",
        iq_order: str = "IQ",
        channel_mode: str = "Complex",
        endianness: str = "Little Endian",
        offset_bytes: int = 0,
        max_samples: Optional[int] = None,
        use_mmap: bool = True,
        **kwargs: Any,
    ) -> SignalRecord:
        SignalValidator.validate_file(filepath)

        if sample_rate is None or sample_rate <= 0:
            raise IncompleteMetadataError(
                "Sample rate is required to ingest raw IQ files.",
                technical_details="Raw IQ files contain no header describing the ADC sampling clock.",
                suggested_action="Specify the sample rate in the File Import Configuration dialog.",
            )

        dt_name = data_type.lower()
        if dt_name not in DTYPE_MAP:
            raise UnsupportedFormatError(f"Unsupported data type: {data_type}")

        raw_dt = DTYPE_MAP[dt_name]
        prefix = "<" if "little" in endianness.lower() else ">"
        np_dtype = np.dtype(f"{prefix}{np.dtype(raw_dt).str[1:]}")

        file_size = filepath.stat().st_size
        bytes_per_val = np_dtype.itemsize
        channels = 2 if channel_mode.lower() == "complex" else 1

        available_bytes = max(0, file_size - offset_bytes)
        available_values = available_bytes // bytes_per_val
        available_samples = available_values // channels

        samples_to_read = available_samples
        if max_samples is not None and max_samples > 0:
            samples_to_read = min(available_samples, max_samples)

        values_to_read = samples_to_read * channels

        # Read or memory-map array
        if use_mmap:
            # Memory map array
            mmap_array = np.memmap(
                filepath,
                dtype=np_dtype,
                mode="r",
                offset=offset_bytes,
                shape=(values_to_read,),
            )
            raw_vals = np.array(mmap_array)
        else:
            with open(filepath, "rb") as f:
                if offset_bytes > 0:
                    f.seek(offset_bytes)
                raw_vals = np.fromfile(f, dtype=np_dtype, count=values_to_read)

        # Normalize integer types to float32 [-1.0, 1.0]
        if np.issubdtype(np_dtype, np.integer):
            info = np.iinfo(raw_dt)
            if np.issubdtype(raw_dt, np.unsignedinteger):
                # e.g. uint8: center at 128
                center = (info.max + 1) / 2.0
                vals_float = (raw_vals.astype(np.float32) - center) / center
            else:
                scale = float(max(abs(info.min), abs(info.max)))
                vals_float = raw_vals.astype(np.float32) / scale
        else:
            vals_float = raw_vals.astype(np.float32)

        # Separate into I and Q
        if channel_mode.lower() == "complex":
            i_vals = vals_float[0::2]
            q_vals = vals_float[1::2]
            if iq_order.upper() == "QI":
                # Swap
                i_vals, q_vals = q_vals, i_vals
            complex_samples = i_vals + 1j * q_vals
            final_channels = 2
        else:
            complex_samples = vals_float
            final_channels = 1

        SignalValidator.validate_samples(complex_samples, allow_real=True)

        meta_sources = {
            "sample_rate": ProvenanceSource.USER,
            "center_frequency": ProvenanceSource.USER if center_frequency is not None else ProvenanceSource.MEASURED,
            "data_type": ProvenanceSource.USER,
        }

        meta = {
            "endianness": endianness,
            "iq_order": iq_order,
            "offset_bytes": offset_bytes,
            "original_dtype": data_type,
        }

        return SignalRecord(
            samples=complex_samples,
            sample_rate=float(sample_rate),
            center_frequency=float(center_frequency or 0.0),
            timestamp=datetime.fromtimestamp(filepath.stat().st_mtime),
            source_file=filepath,
            data_type=data_type,
            channels=final_channels,
            iq_order=iq_order,
            metadata=meta,
            metadata_sources=meta_sources,
        )
