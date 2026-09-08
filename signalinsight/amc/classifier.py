"""Automatic Modulation Classification (AMC) using XGBoost / Random Forest."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

from signalinsight.amc.base import BaseModulationClassifier
from signalinsight.core.constants import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    MOD_16QAM,
    MOD_8PSK,
    MOD_BPSK,
    MOD_FSK,
    MOD_QPSK,
    MOD_UNCERTAIN,
    SUPPORTED_MODULATIONS,
)
from signalinsight.core.models import ModulationResult, SignalRecord
from signalinsight.features.extractor import FeatureExtractor


class XGBoostModulationClassifier(BaseModulationClassifier):
    """
    Production AMC model based on Gradient-Boosted Decision Trees (XGBoost).
    Infers modulation class from normalized statistical, spectral, and cumulant features.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        self.confidence_threshold = confidence_threshold
        self.classes: List[str] = list(SUPPORTED_MODULATIONS)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.idx_to_class = {i: c for i, c in enumerate(self.classes)}
        self.model: Optional[xgb.XGBClassifier] = None
        self.rf_fallback: Optional[RandomForestClassifier] = None
        self.model_name = "XGBoostAMC"
        self.model_version = "1.0.0"
        self.feature_version = "1.0.0"

        if model_path and Path(model_path).exists():
            self.load(Path(model_path))
        else:
            loaded = self._try_load_active_db_model()
            if not loaded:
                radioml_model = Path("data/models/amc_xgboost_radioml.json")
                if radioml_model.exists():
                    self.load(radioml_model)
                    self.model_name = "RadioML2016-XGBoost"
                    self.model_version = "2.0.0"
                else:
                    default_model = Path(__file__).parent / "models" / "amc_xgboost_v1.json"
                    if default_model.exists():
                        self.load(default_model)

    def _try_load_active_db_model(self) -> bool:
        """Attempts to load the currently ACTIVE model record from the database."""
        try:
            from backend.app.db.database import SessionLocal
            from backend.app.db.models.amc import Model
            with SessionLocal() as db:
                active_m = db.query(Model).filter(Model.status == "ACTIVE").order_by(Model.id.desc()).first()
                if active_m and active_m.file_path and Path(active_m.file_path).exists():
                    self.load(Path(active_m.file_path))
                    self.model_name = active_m.name
                    self.model_version = active_m.version
                    if active_m.classes:
                        self.classes = list(active_m.classes)
                        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
                        self.idx_to_class = {i: c for i, c in enumerate(self.classes)}
                    return True
        except Exception:
            pass
        return False

    def get_supported_classes(self) -> List[str]:
        return list(self.classes)

    def train_baseline(self, num_samples_per_class: int = 150, seed: int = 42):
        """
        Trains baseline XGBoost and RF models using synthetic impaired waveforms
        across varying SNR (2 dB to 25 dB) and carrier offsets.
        """
        from signalinsight.amc.synthetic import SyntheticSignalGenerator

        np.random.seed(seed)
        X_list = []
        y_list = []

        snrs = [5.0, 10.0, 15.0, 20.0, 25.0]
        offsets = [-15000.0, 0.0, 15000.0]

        for mod_idx, mod_name in enumerate(self.classes):
            for i in range(num_samples_per_class):
                snr = float(np.random.choice(snrs))
                cfo = float(np.random.choice(offsets))
                phase = float(np.random.uniform(-np.pi, np.pi))
                sym_rate = float(np.random.choice([50000.0, 100000.0, 125000.0]))
                beta = float(np.random.choice([0.25, 0.35, 0.45]))

                rec = SyntheticSignalGenerator.generate(
                    modulation=mod_name,
                    sample_rate=1_000_000.0,
                    symbol_rate=sym_rate,
                    num_symbols=1500,
                    snr_db=snr,
                    carrier_offset_hz=cfo,
                    phase_offset_rad=phase,
                    rrc_beta=beta,
                )

                extracted = FeatureExtractor.extract_all(rec)
                X_list.append(extracted.ml_feature_vector)
                y_list.append(mod_idx)

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.int32)

        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=seed,
            n_jobs=2,
        )
        self.model.fit(X, y)

        # Also train Random Forest fallback
        self.rf_fallback = RandomForestClassifier(
            n_estimators=80,
            max_depth=8,
            random_state=seed,
            n_jobs=2,
        )
        self.rf_fallback.fit(X, y)

    def predict_features(
        self,
        feature_vector: np.ndarray,
        confidence_threshold: Optional[float] = None,
    ) -> ModulationResult:
        if self.model is None and self.rf_fallback is None:
            # Auto-train baseline on first invocation
            self.train_baseline()

        thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        x_in = feature_vector.reshape(1, -1)

        # Predict probabilities
        if self.model is not None:
            probs = self.model.predict_proba(x_in)[0]
            model_name = self.model_name
        else:
            probs = self.rf_fallback.predict_proba(x_in)[0]
            model_name = "RandomForestAMC"

        class_probs = {
            self.idx_to_class[i]: float(probs[i])
            for i in range(len(self.classes))
        }

        best_idx = int(np.argmax(probs))
        best_conf = float(probs[best_idx])
        best_class = self.idx_to_class[best_idx]

        warnings: List[str] = []
        if best_conf < thresh:
            predicted = MOD_UNCERTAIN
            warnings.append(
                f"Max confidence ({best_conf*100:.1f}%) is below rejection threshold ({thresh*100:.1f}%). Marked UNCERTAIN."
            )
        else:
            predicted = best_class

        return ModulationResult(
            predicted_modulation=predicted,
            confidence=best_conf,
            class_probabilities=class_probs,
            model_name=model_name,
            model_version=self.model_version,
            feature_version=self.feature_version,
            warnings=warnings,
        )

    def predict(
        self,
        signal_rec: SignalRecord,
        confidence_threshold: Optional[float] = None,
    ) -> ModulationResult:
        extracted = FeatureExtractor.extract_all(signal_rec)
        return self.predict_features(extracted.ml_feature_vector, confidence_threshold=confidence_threshold)

    def save(self, filepath: Path) -> None:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if self.model is not None:
            self.model.save_model(str(filepath))

    def load(self, filepath: Path) -> None:
        filepath = Path(filepath)
        self.model = xgb.XGBClassifier()
        self.model.load_model(str(filepath))
