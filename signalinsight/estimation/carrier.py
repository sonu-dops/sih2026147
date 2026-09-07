"""Carrier frequency and baseband offset estimation."""

from typing import NamedTuple, Optional
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord
from signalinsight.dsp.fft import FFTEngine
from signalinsight.dsp.psd import PSDEngine
from signalinsight.estimation.base import ParameterEstimator


class CarrierEstimationResult(NamedTuple):
    baseband_frequency_hz: ParameterValue
    rf_carrier_frequency_hz: ParameterValue
    carrier_offset_hz: ParameterValue


class CarrierEstimator(ParameterEstimator):
    """
    Estimates baseband carrier offset and total RF carrier frequency.
    Uses multi-bin quadratic interpolation and prominence-based confidence scoring.
    """

    def estimate(
        self,
        signal_rec: SignalRecord,
        fft_size: int = 4096,
        **kwargs,
    ) -> CarrierEstimationResult:
        fs = signal_rec.sample_rate
        fc_rf_user = signal_rec.center_frequency

        # Compute high-resolution centered spectrum
        spec = FFTEngine.compute_spectrum(
            signal_rec.samples,
            sample_rate=fs,
            fft_size=fft_size,
            window_name="Hann",
            center_freq=0.0,  # Baseband relative
        )

        f_baseband = spec.peak_frequency
        p_peak = spec.peak_power_db

        # Estimate noise floor around peak to judge prominence
        median_p = float(np.median(spec.power_db))
        prominence = p_peak - median_p

        # Confidence heuristic: prominence > 20 dB -> high confidence
        if prominence > 25.0:
            confidence = 0.95
            quality = QualityLevel.HIGH
        elif prominence > 15.0:
            confidence = 0.80
            quality = QualityLevel.MEDIUM
        elif prominence > 6.0:
            confidence = 0.60
            quality = QualityLevel.LOW
        else:
            confidence = 0.30
            quality = QualityLevel.INVALID

        # Calculate RF carrier
        f_rf = fc_rf_user + f_baseband

        rf_source = ProvenanceSource.ESTIMATED
        if fc_rf_user == 0.0 and signal_rec.metadata_sources.get("center_frequency") == ProvenanceSource.MEASURED:
            notes_rf = "Baseband signal (no RF center frequency supplied)"
        else:
            notes_rf = f"Derived from center freq ({fc_rf_user:,.1f} Hz) + baseband offset ({f_baseband:+,.1f} Hz)"

        val_bb = ParameterValue(
            name="Baseband Carrier Offset",
            value=float(f_baseband),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="Windowed FFT + Quadratic Interpolation",
            confidence=confidence,
            quality=quality,
            notes=f"Peak prominence: {prominence:.1f} dB above median",
        )

        val_rf = ParameterValue(
            name="RF Carrier Frequency",
            value=float(f_rf),
            unit="Hz",
            source=rf_source,
            method="Center Frequency + Baseband Offset",
            confidence=confidence,
            quality=quality,
            notes=notes_rf,
        )

        val_offset = ParameterValue(
            name="Carrier Frequency Offset (CFO)",
            value=float(f_baseband),
            unit="Hz",
            source=ProvenanceSource.ESTIMATED,
            method="Peak Spectral Offset",
            confidence=confidence,
            quality=quality,
        )

        return CarrierEstimationResult(
            baseband_frequency_hz=val_bb,
            rf_carrier_frequency_hz=val_rf,
            carrier_offset_hz=val_offset,
        )
