"""Structured application exceptions with actionable diagnostics."""

from typing import Optional


class SignalInsightError(Exception):
    """Base exception for all SignalInsight errors."""

    def __init__(self, message: str, technical_details: Optional[str] = None, suggested_action: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.technical_details = technical_details or ""
        self.suggested_action = suggested_action or "Check application logs for details."

    def __str__(self) -> str:
        s = self.message
        if self.technical_details:
            s += f"\nDetails: {self.technical_details}"
        if self.suggested_action:
            s += f"\nAction: {self.suggested_action}"
        return s


class FileValidationError(SignalInsightError):
    """Raised when file integrity, size, or header validation fails."""
    pass


class UnsupportedFormatError(SignalInsightError):
    """Raised when a file format or data type is not supported."""
    pass


class IncompleteMetadataError(SignalInsightError):
    """Raised when required metadata (e.g. sample rate) is missing and cannot be estimated."""
    pass


class NumericalInstabilityError(SignalInsightError):
    """Raised when NaN, Inf, zero variance, or singular matrix conditions arise in DSP."""
    pass


class CalibrationRequiredError(SignalInsightError):
    """Raised when an operation requires reference calibration (e.g. physical dBm without impedance)."""
    pass


class SynchronizationError(SignalInsightError):
    """Raised when carrier or symbol timing loops fail to converge or diverge."""
    pass


class ClassifierError(SignalInsightError):
    """Raised when AMC model inference fails or features are incompatible."""
    pass


class DecodingUnavailableError(SignalInsightError):
    """Raised when decoding is requested but framing/FEC/CRC parameters are unknown."""
    pass
