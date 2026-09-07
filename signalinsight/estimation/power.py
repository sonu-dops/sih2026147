"""Power, RMS, Crest Factor, and PAPR estimation."""

from typing import NamedTuple, Optional
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord
from signalinsight.estimation.base import ParameterEstimator


class PowerResult(NamedTuple):
    rms_amplitude: ParameterValue
    average_power_dbfs: ParameterValue
    peak_power_dbfs: ParameterValue
    papr_db: ParameterValue
    crest_factor: ParameterValue
    calibrated_power_dbm: ParameterValue


class PowerEstimator(ParameterEstimator):
    """Calculates RMS, Peak Power, Crest Factor, and physical calibration status."""

    def estimate(
        self,
        signal_rec: SignalRecord,
        system_impedance_ohms: Optional[float] = None,
        reference_gain_db: Optional[float] = None,
        **kwargs,
    ) -> PowerResult:
        samples = signal_rec.samples
        abs_sq = np.abs(samples) ** 2
        p_avg = float(np.mean(abs_sq))
        p_peak = float(np.max(abs_sq))
        rms_val = float(np.sqrt(p_avg))

        # Relative dBFS (Full Scale = 1.0 peak)
        p_avg_dbfs = 10.0 * np.log10(max(p_avg, 1e-15))
        p_peak_dbfs = 10.0 * np.log10(max(p_peak, 1e-15))

        # PAPR and Crest factor
        papr_db = max(0.0, p_peak_dbfs - p_avg_dbfs)
        crest_factor = float(np.sqrt(p_peak) / max(rms_val, 1e-15))

        val_rms = ParameterValue(
            name="RMS Amplitude",
            value=rms_val,
            unit="FS",
            source=ProvenanceSource.CALCULATED,
            method="sqrt(mean(|x|^2))",
            confidence=1.0,
            quality=QualityLevel.HIGH,
        )

        val_p_avg = ParameterValue(
            name="Average Power",
            value=p_avg_dbfs,
            unit="dBFS",
            source=ProvenanceSource.CALCULATED,
            method="10*log10(mean(|x|^2))",
            confidence=1.0,
            quality=QualityLevel.HIGH,
        )

        val_p_peak = ParameterValue(
            name="Peak Power",
            value=p_peak_dbfs,
            unit="dBFS",
            source=ProvenanceSource.CALCULATED,
            method="10*log10(max(|x|^2))",
            confidence=1.0,
            quality=QualityLevel.HIGH,
        )

        val_papr = ParameterValue(
            name="PAPR",
            value=papr_db,
            unit="dB",
            source=ProvenanceSource.CALCULATED,
            method="Peak-to-Average Power Ratio",
            confidence=1.0,
            quality=QualityLevel.HIGH,
        )

        val_crest = ParameterValue(
            name="Crest Factor",
            value=crest_factor,
            unit="ratio",
            source=ProvenanceSource.CALCULATED,
            method="Peak / RMS",
            confidence=1.0,
            quality=QualityLevel.HIGH,
        )

        # Calibrated dBm calculation ONLY if impedance & gain are supplied
        if system_impedance_ohms is not None and reference_gain_db is not None:
            # P_watts = (V_rms^2) / R
            # dBm = 10*log10(P_watts * 1000) - gain
            p_watts = (rms_val ** 2) / system_impedance_ohms
            dbm_val = 10.0 * np.log10(max(p_watts * 1000.0, 1e-12)) - reference_gain_db
            val_dbm = ParameterValue(
                name="Calibrated Power",
                value=float(dbm_val),
                unit="dBm",
                source=ProvenanceSource.MEASURED,
                method=f"V_rms^2 / R (R={system_impedance_ohms}Ω, Gain={reference_gain_db}dB)",
                confidence=0.98,
                quality=QualityLevel.HIGH,
            )
        else:
            val_dbm = ParameterValue(
                name="Calibrated Power",
                value=None,
                unit="dBm",
                source=ProvenanceSource.CALIBRATION_REQUIRED,
                method="Requires Reference Impedance & RF Frontend Gain Calibration",
                confidence=0.0,
                quality=QualityLevel.INVALID,
                notes="Arbitrary dBm values are never fabricated for uncalibrated raw IQ/WAV data.",
            )

        return PowerResult(
            rms_amplitude=val_rms,
            average_power_dbfs=val_p_avg,
            peak_power_dbfs=val_p_peak,
            papr_db=val_papr,
            crest_factor=val_crest,
            calibrated_power_dbm=val_dbm,
        )
