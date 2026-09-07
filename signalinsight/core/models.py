"""Data models and common signal representations with scientific provenance."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
from pydantic import BaseModel, Field, ConfigDict


class ProvenanceSource(str, Enum):
    """Provenance tracking for all parameters and metadata."""
    SIGMF = "SIGMF"
    USER = "USER"
    ESTIMATED = "ESTIMATED"
    CALCULATED = "CALCULATED"
    MEASURED = "MEASURED"
    UNAVAILABLE = "UNAVAILABLE"
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"


class QualityLevel(str, Enum):
    """Quality / confidence indicator."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INVALID = "INVALID"


class ParameterValue(BaseModel):
    """Represents a measured, calculated, or estimated signal parameter with full provenance."""
    name: str
    value: Optional[Union[float, int, str, bool]] = None
    unit: str = ""
    source: ProvenanceSource = ProvenanceSource.UNAVAILABLE
    method: str = "N/A"
    confidence: float = 0.0  # Normalized 0.0 to 1.0
    quality: QualityLevel = QualityLevel.INVALID
    notes: Optional[str] = None

    def display_str(self) -> str:
        """Format for technical UI displays."""
        if self.value is None or (isinstance(self.value, float) and np.isnan(self.value)):
            return f"N/A [{self.source.value}]"
        if isinstance(self.value, float):
            # Format frequency or large numbers with engineering scale
            val_str = f"{self.value:,.4f}".rstrip('0').rstrip('.')
            return f"{val_str} {self.unit} [{self.source.value}]"
        return f"{self.value} {self.unit} [{self.source.value}]"


class ProcessingStepRecord(BaseModel):
    """Audit record for a single transformation in the DSP pipeline."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    status: str = "SUCCESS"
    notes: Optional[str] = None


class MarkerType(str, Enum):
    FREQUENCY = "Frequency"
    TIME = "Time"
    AMPLITUDE = "Amplitude"
    DELTA = "Delta"
    PEAK = "Peak"
    BANDWIDTH = "Bandwidth"


class Marker(BaseModel):
    """Interactive graph marker."""
    id: str
    marker_type: MarkerType
    position: float
    value: float
    units: str
    source_plot: str
    reference_marker_id: Optional[str] = None


class SignalRecord:
    """
    Common internal representation for all ingested signals.
    Decouples raw file loaders from downstream DSP algorithms.
    """

    def __init__(
        self,
        samples: np.ndarray,
        sample_rate: float,
        center_frequency: float = 0.0,
        timestamp: Optional[datetime] = None,
        source_file: Optional[Path] = None,
        data_type: str = "complex64",
        channels: int = 1,
        iq_order: str = "IQ",
        metadata: Optional[Dict[str, Any]] = None,
        metadata_sources: Optional[Dict[str, ProvenanceSource]] = None,
    ):
        if samples is None or len(samples) == 0:
            raise ValueError("Cannot initialize SignalRecord with empty samples.")

        # Ensure 1D complex or float array
        if samples.ndim > 1 and samples.shape[1] == 2:
            # Interleaved or 2-column IQ
            samples = samples[:, 0] + 1j * samples[:, 1]
        elif samples.ndim > 1:
            samples = samples.flatten()

        self.samples: np.ndarray = samples
        self.sample_rate: float = float(sample_rate)
        self.center_frequency: float = float(center_frequency)
        self.timestamp: datetime = timestamp or datetime.utcnow()
        self.source_file: Optional[Path] = Path(source_file) if source_file else None
        self.data_type: str = data_type
        self.channels: int = channels
        self.iq_order: str = iq_order
        self.metadata: Dict[str, Any] = metadata or {}
        self.metadata_sources: Dict[str, ProvenanceSource] = metadata_sources or {}
        self.processing_history: List[ProcessingStepRecord] = []

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def duration(self) -> float:
        if self.sample_rate > 0:
            return self.sample_count / self.sample_rate
        return 0.0

    @property
    def is_complex(self) -> bool:
        return np.iscomplexobj(self.samples)

    def copy(self) -> SignalRecord:
        """Create a deep copy of the signal record and samples."""
        new_rec = SignalRecord(
            samples=np.copy(self.samples),
            sample_rate=self.sample_rate,
            center_frequency=self.center_frequency,
            timestamp=self.timestamp,
            source_file=self.source_file,
            data_type=self.data_type,
            channels=self.channels,
            iq_order=self.iq_order,
            metadata=dict(self.metadata),
            metadata_sources=dict(self.metadata_sources),
        )
        new_rec.processing_history = [
            ProcessingStepRecord(**step.model_dump()) for step in self.processing_history
        ]
        return new_rec

    def add_history(self, stage: str, params: Dict[str, Any], elapsed_ms: float, notes: Optional[str] = None):
        self.processing_history.append(
            ProcessingStepRecord(
                stage=stage,
                parameters=params,
                execution_time_ms=elapsed_ms,
                notes=notes,
            )
        )


class ModulationResult(BaseModel):
    """Output from Automatic Modulation Classification."""
    predicted_modulation: str
    confidence: float
    class_probabilities: Dict[str, float] = Field(default_factory=dict)
    model_name: str = "XGBoostAMC"
    model_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    warnings: List[str] = Field(default_factory=list)


class SynchronizationResult(BaseModel):
    """Output from carrier & symbol timing recovery."""
    converged: bool = False
    carrier_frequency_offset_hz: ParameterValue = Field(
        default_factory=lambda: ParameterValue(name="CFO", unit="Hz")
    )
    phase_offset_rad: ParameterValue = Field(
        default_factory=lambda: ParameterValue(name="Phase Offset", unit="rad")
    )
    timing_offset_samples: ParameterValue = Field(
        default_factory=lambda: ParameterValue(name="Timing Error", unit="samples")
    )
    algorithm: str = "None"
    notes: Optional[str] = None


class DemodulationResult(BaseModel):
    """Output from digital demodulator."""
    modulation: str
    symbol_count: int = 0
    symbols: List[complex] = Field(default_factory=list)
    bits: List[int] = Field(default_factory=list)
    evm_rms_pct: Optional[ParameterValue] = None
    evm_peak_pct: Optional[ParameterValue] = None
    iq_imbalance_db: Optional[ParameterValue] = None
    quadrature_skew_deg: Optional[ParameterValue] = None
    notes: Optional[str] = None


class DecodingResult(BaseModel):
    """Output from optional forward error correction / CRC framework."""
    available: bool = False
    fec_type: str = "None"
    code_rate: str = "None"
    crc_valid: Optional[bool] = None
    decoded_payload: Optional[str] = None
    bit_count: int = 0
    message: str = "Decoding unavailable — coding configuration not specified."


class AnalysisResult(BaseModel):
    """
    Comprehensive structured output container for all analysis results.
    Preserves complete provenance, configurations, and timing.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_file: str = "N/A"
    file_hash_sha256: str = "N/A"
    sample_rate: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Sample Rate", unit="Hz"))
    center_frequency: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Center Frequency", unit="Hz"))
    duration_s: float = 0.0
    sample_count: int = 0

    # DC & Power
    dc_offset_i: ParameterValue = Field(default_factory=lambda: ParameterValue(name="I DC Offset", unit="V"))
    dc_offset_q: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Q DC Offset", unit="V"))
    signal_power: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Signal Power (Rel)", unit="dBFS"))
    noise_floor: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Noise Floor", unit="dBFS/Hz"))
    snr_db: ParameterValue = Field(default_factory=lambda: ParameterValue(name="SNR", unit="dB"))

    # Spectral
    occupied_bw_99: ParameterValue = Field(default_factory=lambda: ParameterValue(name="99% OBW", unit="Hz"))
    bandwidth_3db: ParameterValue = Field(default_factory=lambda: ParameterValue(name="3 dB Bandwidth", unit="Hz"))
    carrier_frequency: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Carrier Frequency", unit="Hz"))
    carrier_offset: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Carrier Offset", unit="Hz"))
    symbol_rate: ParameterValue = Field(default_factory=lambda: ParameterValue(name="Symbol Rate", unit="Baud"))

    # Features & Classification
    features: Dict[str, ParameterValue] = Field(default_factory=dict)
    cumulants: Dict[str, ParameterValue] = Field(default_factory=dict)
    modulation_result: Optional[ModulationResult] = None

    # Sync, Demod, Decode
    synchronization_result: Optional[SynchronizationResult] = None
    demodulation_result: Optional[DemodulationResult] = None
    decoding_result: Optional[DecodingResult] = None

    # Diagnostics
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    processing_times_ms: Dict[str, float] = Field(default_factory=dict)
