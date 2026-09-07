"""Signal and file validation routines."""

from pathlib import Path
from typing import Optional
import numpy as np
from signalinsight.core.exceptions import FileValidationError, NumericalInstabilityError


class SignalValidator:
    """Validates files, metadata, and numerical integrity."""

    @staticmethod
    def validate_file(filepath: Path, max_size_bytes: Optional[int] = None) -> None:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileValidationError(
                f"File not found: {filepath.name}",
                technical_details=f"Absolute path does not exist: {filepath}",
                suggested_action="Verify that the file path is correct and accessible.",
            )

        if not filepath.is_file():
            raise FileValidationError(
                f"Path is not a regular file: {filepath.name}",
                technical_details=f"Target path is a directory or special device: {filepath}",
                suggested_action="Select a valid recording file (.iq, .wav, .sigmf-meta).",
            )

        file_size = filepath.stat().st_size
        if file_size == 0:
            raise FileValidationError(
                f"File is empty: {filepath.name}",
                technical_details="File size is 0 bytes.",
                suggested_action="Ensure the recording was saved properly and has non-zero size.",
            )

        if max_size_bytes and file_size > max_size_bytes:
            raise FileValidationError(
                f"File exceeds maximum allowed size ({file_size / (1024**3):.2f} GB > {max_size_bytes / (1024**3):.2f} GB)",
                suggested_action="Use chunked streaming mode or select a smaller slice.",
            )

    @staticmethod
    def validate_samples(samples: np.ndarray, allow_real: bool = True) -> None:
        """Verify numerical stability of sample array."""
        if samples is None or len(samples) == 0:
            raise NumericalInstabilityError(
                "Sample array is empty.",
                suggested_action="Provide a non-empty signal buffer.",
            )

        if not allow_real and not np.iscomplexobj(samples):
            raise NumericalInstabilityError(
                "Complex IQ signal required, but real-valued samples were provided.",
                suggested_action="Convert real signal to analytic complex representation using Hilbert transform.",
            )

        # Check for NaN and Inf
        if np.iscomplexobj(samples):
            has_nan = np.isnan(samples.real).any() or np.isnan(samples.imag).any()
            has_inf = np.isinf(samples.real).any() or np.isinf(samples.imag).any()
        else:
            has_nan = np.isnan(samples).any()
            has_inf = np.isinf(samples).any()

        if has_nan:
            raise NumericalInstabilityError(
                "Sample array contains NaN (Not-a-Number) values.",
                suggested_action="Check file integrity or ADC calibration for buffer corruption.",
            )

        if has_inf:
            raise NumericalInstabilityError(
                "Sample array contains Infinite values (Inf).",
                suggested_action="Verify numerical scaling and dynamic range limits.",
            )

    @staticmethod
    def validate_sample_rate(sample_rate: Optional[float]) -> float:
        if sample_rate is None or sample_rate <= 0:
            raise FileValidationError(
                "Invalid sample rate.",
                technical_details=f"Sample rate must be positive, got: {sample_rate}",
                suggested_action="Specify the sample rate in the File Import Configuration dialog.",
            )
        return float(sample_rate)
