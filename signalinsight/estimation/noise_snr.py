"""Robust noise floor and Signal-to-Noise Ratio (SNR) estimation."""

from typing import NamedTuple, Optional
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel, SignalRecord
from signalinsight.dsp.psd import PSDEngine, PSDResult
from signalinsight.estimation.base import ParameterEstimator


class NoiseSNRResult(NamedTuple):
    snr_db: ParameterValue
    signal_power: ParameterValue
    noise_power: ParameterValue
    noise_floor_dbfs_hz: ParameterValue


class NoiseSNREstimator(ParameterEstimator):
    """
    Estimates noise floor and in-band SNR using percentile statistics
    and spectral energy partition.
    """

    def estimate(
        self,
        signal_rec: SignalRecord,
        percentile: float = 15.0,
        nperseg: int = 2048,
        **kwargs,
    ) -> NoiseSNRResult:
        psd_res: PSDResult = PSDEngine.compute_psd(
            signal_rec.samples,
            sample_rate=signal_rec.sample_rate,
            nperseg=nperseg,
        )

        psd_lin = psd_res.psd_linear
        psd_db = psd_res.psd_db_hz
        df = psd_res.frequencies[1] - psd_res.frequencies[0] if len(psd_res.frequencies) > 1 else 1.0
        bw_total = signal_rec.sample_rate

        # Robust noise floor density (Watts/Hz) via lower percentile of PSD bins
        # Bins below the 15th percentile represent unmodulated noise floor
        noise_density_lin = float(np.percentile(psd_lin, percentile))
        noise_floor_db = 10.0 * np.log10(max(noise_density_lin, 1e-18))

        # Total integrated noise power across full Nyquist band
        total_noise_power = noise_density_lin * bw_total

        # Total signal + noise power
        total_measured_power = psd_res.total_power

        # Extracted signal power
        signal_power = max(1e-18, total_measured_power - total_noise_power)

        # In-band SNR
        if total_noise_power > 0 and signal_power > 1e-15:
            snr_linear = signal_power / total_noise_power
            snr_val = float(10.0 * np.log10(max(snr_linear, 1e-6)))
        else:
            snr_val = -30.0

        # Confidence based on SNR value
        if snr_val > 10.0:
            confidence = 0.95
            quality = QualityLevel.HIGH
        elif snr_val > 0.0:
            confidence = 0.80
            quality = QualityLevel.MEDIUM
        elif snr_val > -10.0:
            confidence = 0.60
            quality = QualityLevel.LOW
        else:
            confidence = 0.40
            quality = QualityLevel.INVALID

        val_snr = ParameterValue(
            name="SNR",
            value=float(snr_val),
            unit="dB",
            source=ProvenanceSource.ESTIMATED,
            method=f"PSD Spectral Integration ({percentile}th percentile floor)",
            confidence=confidence,
            quality=quality,
            notes=f"Signal power: {10*np.log10(signal_power):.2f} dBFS, Noise: {10*np.log10(total_noise_power):.2f} dBFS",
        )

        val_sig_p = ParameterValue(
            name="Signal Power",
            value=float(10.0 * np.log10(signal_power)),
            unit="dBFS",
            source=ProvenanceSource.ESTIMATED,
            method="In-band Spectral Integration",
            confidence=confidence,
            quality=quality,
        )

        val_noise_p = ParameterValue(
            name="Noise Power",
            value=float(10.0 * np.log10(max(total_noise_power, 1e-18))),
            unit="dBFS",
            source=ProvenanceSource.ESTIMATED,
            method=f"Integrated {percentile}th Percentile Floor",
            confidence=confidence,
            quality=quality,
        )

        val_floor = ParameterValue(
            name="Noise Floor",
            value=float(noise_floor_db),
            unit="dBFS/Hz",
            source=ProvenanceSource.ESTIMATED,
            method=f"{percentile}th Percentile Spectral Density",
            confidence=confidence,
            quality=quality,
        )

        return NoiseSNRResult(
            snr_db=val_snr,
            signal_power=val_sig_p,
            noise_power=val_noise_p,
            noise_floor_dbfs_hz=val_floor,
        )
