"""PipelineRunner orchestrating end-to-end signal analysis."""

from datetime import datetime
import hashlib
import time
from typing import Callable, Dict, List, Optional
import numpy as np

from signalinsight.amc.classifier import XGBoostModulationClassifier
from signalinsight.core.constants import MOD_16QAM, MOD_8PSK, MOD_BPSK, MOD_FSK, MOD_QPSK, MOD_UNCERTAIN
from signalinsight.core.logging import logger
from signalinsight.core.models import (
    AnalysisResult,
    DecodingResult,
    DemodulationResult,
    ModulationResult,
    ParameterValue,
    ProvenanceSource,
    QualityLevel,
    SignalRecord,
    SynchronizationResult,
)
from signalinsight.decoding.fec import ConfiguredFECDecoder
from signalinsight.demodulation.fsk import FSKDemodulator
from signalinsight.demodulation.psk import BPSKDemodulator, EightPSKDemodulator, QPSKDemodulator
from signalinsight.demodulation.qam import QAM16Demodulator
from signalinsight.dsp.preprocessing import NormalizationMode, SignalPreprocessor
from signalinsight.estimation.bandwidth import BandwidthEstimator
from signalinsight.estimation.carrier import CarrierEstimator
from signalinsight.estimation.noise_snr import NoiseSNREstimator
from signalinsight.estimation.power import PowerEstimator
from signalinsight.estimation.symbol_rate import SymbolRateEstimator
from signalinsight.features.extractor import FeatureExtractor
from signalinsight.synchronization.carrier_sync import CarrierSynchronizer
from signalinsight.synchronization.matched_filter import MatchedFilterProcessor
from signalinsight.synchronization.timing_sync import GardnerTimingRecovery


class PipelineOptions:
    """Configuration options for pipeline execution."""

    def __init__(
        self,
        remove_dc: bool = True,
        normalize_rms: bool = False,
        estimate_parameters: bool = True,
        extract_features: bool = True,
        run_amc: bool = True,
        run_sync: bool = True,
        run_demod: bool = True,
        run_decode: bool = False,
        target_modulation: Optional[str] = "Auto",
        confidence_threshold: float = 0.65,
        fec_type: str = "None",
    ):
        self.remove_dc = remove_dc
        self.normalize_rms = normalize_rms
        self.estimate_parameters = estimate_parameters
        self.extract_features = extract_features
        self.run_amc = run_amc
        self.run_sync = run_sync
        self.run_demod = run_demod
        self.run_decode = run_decode
        self.target_modulation = target_modulation
        self.confidence_threshold = confidence_threshold
        self.fec_type = fec_type


class PipelineRunner:
    """Executes the complete analysis pipeline sequentially with full audit tracking."""

    def __init__(self, classifier: Optional[XGBoostModulationClassifier] = None):
        self.classifier = classifier or XGBoostModulationClassifier()
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(
        self,
        signal_rec: SignalRecord,
        options: Optional[PipelineOptions] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> AnalysisResult:
        self._is_cancelled = False
        opts = options or PipelineOptions()
        t_start_total = time.perf_counter()
        timing_records: Dict[str, float] = {}
        warnings: List[str] = []
        errors: List[str] = []

        def report(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)
            logger.info("Pipeline", f"[{pct}%] {msg}")

        # Compute file hash
        file_hash = "N/A"
        if signal_rec.source_file and signal_rec.source_file.exists():
            try:
                with open(signal_rec.source_file, "rb") as f:
                    file_hash = hashlib.sha256(f.read(65536)).hexdigest()
            except Exception:
                pass

        current_sig = signal_rec.copy()

        # ----------------------------------------------------
        # Stage 1: Preprocessing (DC Removal & Normalization)
        # ----------------------------------------------------
        report(10, "Preprocessing & DC offset correction...")
        t0 = time.perf_counter()
        dc_i_val = 0.0
        dc_q_val = 0.0

        if opts.remove_dc:
            current_sig, dc_res = SignalPreprocessor.remove_dc_offset(current_sig)
            dc_i_val = dc_res.offset_i
            dc_q_val = dc_res.offset_q

        if opts.normalize_rms:
            current_sig = SignalPreprocessor.normalize(current_sig, mode=NormalizationMode.RMS)

        timing_records["preprocessing"] = (time.perf_counter() - t0) * 1000.0

        if self._is_cancelled:
            raise InterruptedError("Analysis cancelled by user.")

        # ----------------------------------------------------
        # Stage 2: Parameter Estimation
        # ----------------------------------------------------
        report(25, "Estimating carrier, bandwidth, and noise...")
        t0 = time.perf_counter()

        carrier_res = CarrierEstimator().estimate(current_sig)
        bw_res = BandwidthEstimator().estimate(current_sig)
        noise_res = NoiseSNREstimator().estimate(current_sig)
        power_res = PowerEstimator().estimate(current_sig)
        sym_res = SymbolRateEstimator().estimate(current_sig)

        timing_records["parameter_estimation"] = (time.perf_counter() - t0) * 1000.0

        if self._is_cancelled:
            raise InterruptedError("Analysis cancelled by user.")

        # ----------------------------------------------------
        # Stage 3: Feature Extraction
        # ----------------------------------------------------
        report(45, "Extracting statistical, spectral, and cumulant features...")
        t0 = time.perf_counter()

        extracted = FeatureExtractor.extract_all(current_sig)
        timing_records["feature_extraction"] = (time.perf_counter() - t0) * 1000.0

        if self._is_cancelled:
            raise InterruptedError("Analysis cancelled by user.")

        # ----------------------------------------------------
        # Stage 4: Automatic Modulation Classification (AMC)
        # ----------------------------------------------------
        report(65, "Running Automatic Modulation Classification...")
        t0 = time.perf_counter()
        mod_result: Optional[ModulationResult] = None

        if opts.run_amc:
            mod_result = self.classifier.predict_features(
                extracted.ml_feature_vector,
                confidence_threshold=opts.confidence_threshold,
            )
            detected_mod = mod_result.predicted_modulation
        else:
            detected_mod = opts.target_modulation or "QPSK"

        timing_records["amc"] = (time.perf_counter() - t0) * 1000.0

        # Determine effective modulation for sync and demod
        effective_mod = detected_mod
        if opts.target_modulation and opts.target_modulation.upper() != "AUTO":
            effective_mod = opts.target_modulation.upper()

        if self._is_cancelled:
            raise InterruptedError("Analysis cancelled by user.")

        # ----------------------------------------------------
        # Stage 5: Synchronization
        # ----------------------------------------------------
        report(80, f"Synchronizing carrier and symbol timing ({effective_mod})...")
        t0 = time.perf_counter()
        sync_result: Optional[SynchronizationResult] = None
        demod_symbols = current_sig.samples

        if opts.run_sync and effective_mod != MOD_UNCERTAIN and effective_mod != MOD_FSK:
            try:
                # 1. Carrier sync via Costas Loop
                synced_sig, sync_result = CarrierSynchronizer.synchronize(
                    current_sig,
                    modulation=effective_mod,
                )
                # 2. Timing recovery
                est_rate = sym_res.symbol_rate_baud.value
                if est_rate and est_rate > 0:
                    sps = max(2, int(round(current_sig.sample_rate / est_rate)))
                    timing_res = GardnerTimingRecovery().recover(synced_sig.samples, samples_per_symbol=sps)
                    if len(timing_res.symbol_samples) > 0:
                        demod_symbols = timing_res.symbol_samples
                else:
                    demod_symbols = synced_sig.samples
            except Exception as e:
                warnings.append(f"Synchronization fallback: {e}")
                demod_symbols = current_sig.samples

        timing_records["synchronization"] = (time.perf_counter() - t0) * 1000.0

        if self._is_cancelled:
            raise InterruptedError("Analysis cancelled by user.")

        # ----------------------------------------------------
        # Stage 6: Demodulation
        # ----------------------------------------------------
        report(90, f"Demodulating symbols ({effective_mod})...")
        t0 = time.perf_counter()
        demod_result: Optional[DemodulationResult] = None

        if opts.run_demod and effective_mod != MOD_UNCERTAIN:
            try:
                if effective_mod == MOD_BPSK:
                    demod_result = BPSKDemodulator().demodulate(demod_symbols)
                elif effective_mod == MOD_QPSK:
                    demod_result = QPSKDemodulator().demodulate(demod_symbols)
                elif effective_mod == MOD_8PSK:
                    demod_result = EightPSKDemodulator().demodulate(demod_symbols)
                elif effective_mod in (MOD_16QAM, "16QAM"):
                    demod_result = QAM16Demodulator().demodulate(demod_symbols)
                elif effective_mod == MOD_FSK:
                    demod_result = FSKDemodulator(
                        sample_rate=current_sig.sample_rate,
                        symbol_rate=sym_res.symbol_rate_baud.value or 100e3,
                    ).demodulate(current_sig.samples)
            except Exception as e:
                warnings.append(f"Demodulation exception: {e}")

        timing_records["demodulation"] = (time.perf_counter() - t0) * 1000.0

        # ----------------------------------------------------
        # Stage 7: Decoding (FEC / Framing)
        # ----------------------------------------------------
        report(95, "Evaluating decoding and framing configuration...")
        t0 = time.perf_counter()
        decoding_result: Optional[DecodingResult] = None

        bits_to_decode = demod_result.bits if demod_result else []
        decoder = ConfiguredFECDecoder(fec_type=opts.fec_type if opts.run_decode else "None")
        decoding_result = decoder.decode(bits_to_decode)

        timing_records["decoding"] = (time.perf_counter() - t0) * 1000.0

        report(100, "Analysis complete.")

        # Total elapsed
        timing_records["total_pipeline_ms"] = (time.perf_counter() - t_start_total) * 1000.0

        # Assemble full AnalysisResult
        return AnalysisResult(
            session_id=logger.session_id,
            timestamp=datetime.utcnow(),
            source_file=str(signal_rec.source_file) if signal_rec.source_file else "MemoryBuffer",
            file_hash_sha256=file_hash,
            sample_rate=ParameterValue(
                name="Sample Rate",
                value=signal_rec.sample_rate,
                unit="Hz",
                source=signal_rec.metadata_sources.get("sample_rate", ProvenanceSource.MEASURED),
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            center_frequency=ParameterValue(
                name="Center Frequency",
                value=signal_rec.center_frequency,
                unit="Hz",
                source=signal_rec.metadata_sources.get("center_frequency", ProvenanceSource.MEASURED),
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            duration_s=signal_rec.duration,
            sample_count=signal_rec.sample_count,
            dc_offset_i=ParameterValue(
                name="I DC Offset",
                value=float(dc_i_val),
                unit="V",
                source=ProvenanceSource.CALCULATED,
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            dc_offset_q=ParameterValue(
                name="Q DC Offset",
                value=float(dc_q_val),
                unit="V",
                source=ProvenanceSource.CALCULATED,
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            signal_power=noise_res.signal_power,
            noise_floor=noise_res.noise_floor_dbfs_hz,
            snr_db=noise_res.snr_db,
            occupied_bw_99=bw_res.obw_99_hz,
            bandwidth_3db=bw_res.bandwidth_3db_hz,
            carrier_frequency=carrier_res.rf_carrier_frequency_hz,
            carrier_offset=carrier_res.carrier_offset_hz,
            symbol_rate=sym_res.symbol_rate_baud,
            features=extracted.all_features,
            cumulants=extracted.cumulant_features,
            modulation_result=mod_result,
            synchronization_result=sync_result,
            demodulation_result=demod_result,
            decoding_result=decoding_result,
            warnings=warnings,
            errors=errors,
            processing_times_ms=timing_records,
        )
