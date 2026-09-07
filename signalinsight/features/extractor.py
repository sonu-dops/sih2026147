"""Unified feature extraction coordinator for AMC and signal analysis."""

from typing import Dict, List, NamedTuple, Tuple
import numpy as np

from signalinsight.core.models import ParameterValue, SignalRecord
from signalinsight.dsp.analytic import AnalyticSignalEngine
from signalinsight.features.cumulants import CumulantsCalculator
from signalinsight.features.iq_features import IQFeaturesCalculator
from signalinsight.features.phase_freq_features import PhaseFrequencyFeaturesCalculator
from signalinsight.features.spectral_features import SpectralFeaturesCalculator
from signalinsight.features.time_features import TimeFeaturesCalculator


class ExtractedFeatures(NamedTuple):
    all_features: Dict[str, ParameterValue]
    cumulant_features: Dict[str, ParameterValue]
    ml_feature_vector: np.ndarray
    ml_feature_names: List[str]


class FeatureExtractor:
    """Extracts the complete feature set across time, envelope, phase, freq, spectral, and HOC domains."""

    FEATURE_VECTOR_KEYS = [
        "f40",
        "f41",
        "f42",
        "norm_envelope_var",
        "envelope_par",
        "envelope_skewness",
        "envelope_kurtosis",
        "phase_variance",
        "phase_jump_rate",
        "freq_std",
        "freq_mean_deviation",
        "freq_kurtosis",
        "spectral_spread",
        "spectral_flatness",
        "zero_crossing_rate_i",
        "iq_correlation",
        "iq_amplitude_imbalance_db",
    ]

    @classmethod
    def extract_all(cls, signal_rec: SignalRecord) -> ExtractedFeatures:
        samples = signal_rec.samples
        fs = signal_rec.sample_rate

        # Ensure analytic representation if real
        analytic = AnalyticSignalEngine.to_analytic(samples)

        # 1. Cumulants
        hoc_res = CumulantsCalculator.compute(analytic)

        # 2. Time & Envelope
        time_feats = TimeFeaturesCalculator.compute(analytic)

        # 3. Phase & Frequency
        phase_freq_feats = PhaseFrequencyFeaturesCalculator.compute(analytic, sample_rate=fs)

        # 4. Spectral
        spectral_feats = SpectralFeaturesCalculator.compute(analytic, sample_rate=fs)

        # 5. IQ
        iq_feats = IQFeaturesCalculator.compute(analytic)

        # Merge dictionaries
        combined: Dict[str, ParameterValue] = {}
        combined.update(hoc_res.feature_dict)
        combined.update(time_feats)
        combined.update(phase_freq_feats)
        combined.update(spectral_feats)
        combined.update(iq_feats)

        # Build consistent numerical vector for AMC ML models
        vector_vals: List[float] = []
        for key in cls.FEATURE_VECTOR_KEYS:
            if key in combined and combined[key].value is not None:
                val = float(combined[key].value)
                # Safeguard against NaN/Inf in feature vector
                if np.isnan(val) or np.isinf(val):
                    val = 0.0
                vector_vals.append(val)
            else:
                vector_vals.append(0.0)

        ml_vector = np.array(vector_vals, dtype=np.float32)

        return ExtractedFeatures(
            all_features=combined,
            cumulant_features=hoc_res.feature_dict,
            ml_feature_vector=ml_vector,
            ml_feature_names=list(cls.FEATURE_VECTOR_KEYS),
        )
