"""Model training, evaluation, and serialization routine for SignalInsight AMC.

Supports:
1. Synthetic generation across customizable SNR and channel impairment grids.
2. Directory-based datasets (folder per modulation class containing .wav / .iq files).
3. Benchmark datasets (e.g., RadioML 2016.10a pickle dictionaries).
"""

import argparse
from datetime import datetime
import os
from pathlib import Path
import pickle
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import xgboost as xgb

from signalinsight.amc.classifier import XGBoostModulationClassifier
from signalinsight.amc.synthetic import SyntheticSignalGenerator
from signalinsight.core.constants import (
    MOD_16QAM,
    MOD_8PSK,
    MOD_BPSK,
    MOD_FSK,
    MOD_QPSK,
    SUPPORTED_MODULATIONS,
)
from signalinsight.core.logging import logger
from signalinsight.core.models import SignalRecord
from signalinsight.features.extractor import FeatureExtractor
from signalinsight.io.iq_loader import RawIQSignalLoader
from signalinsight.io.wav_loader import WavSignalLoader


def load_from_synthetic(
    num_samples_per_class: int = 200,
    snr_range: Tuple[float, float] = (0.0, 30.0),
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Generates synthetic training dataset with diverse SNRs, CFOs, phases, and symbol rates."""
    classes = list(SUPPORTED_MODULATIONS)
    X_list = []
    y_list = []

    np.random.seed(seed)
    snr_vals = np.linspace(snr_range[0], snr_range[1], 7)
    cfo_vals = [-25000.0, -10000.0, 0.0, 10000.0, 25000.0]
    symbol_rates = [25000.0, 50000.0, 100000.0, 125000.0]
    rrc_betas = [0.20, 0.25, 0.35, 0.45]

    print(f"[*] Generating synthetic signals for {len(classes)} classes ({num_samples_per_class} per class)...")
    for mod_idx, mod_name in enumerate(classes):
        for i in range(num_samples_per_class):
            snr = float(np.random.choice(snr_vals))
            cfo = float(np.random.choice(cfo_vals))
            phase = float(np.random.uniform(-np.pi, np.pi))
            sym_rate = float(np.random.choice(symbol_rates))
            beta = float(np.random.choice(rrc_betas))

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

            feat = FeatureExtractor.extract_all(rec)
            X_list.append(feat.ml_feature_vector)
            y_list.append(mod_idx)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y, classes


def load_from_directory(
    dataset_dir: Path,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads recordings from a directory where subfolders represent modulation classes:
    dataset_dir/
      ├── BPSK/  (*.wav, *.iq)
      ├── QPSK/
      ├── 8PSK/
      ├── 16-QAM/
      └── FSK/
    """
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
    if not subdirs:
        raise ValueError(f"No class subfolders found inside {dataset_dir}")

    classes = [d.name.upper() for d in subdirs]
    class_to_idx = {c: i for i, c in enumerate(classes)}

    wav_loader = WavSignalLoader()
    iq_loader = RawIQSignalLoader()

    X_list = []
    y_list = []

    print(f"[*] Scanning class directories: {classes}")
    for d in subdirs:
        mod_name = d.name.upper()
        mod_idx = class_to_idx[mod_name]
        files = list(d.glob("*.wav")) + list(d.glob("*.iq")) + list(d.glob("*.sigmf-meta"))
        print(f"    - {mod_name}: Found {len(files)} signal files")

        for f in files:
            try:
                if f.suffix.lower() == ".wav":
                    rec = wav_loader.load(f)
                elif f.suffix.lower() in (".iq", ".raw", ".bin"):
                    rec = iq_loader.load(f, sample_rate=1e6)
                elif "sigmf" in f.name.lower():
                    from signalinsight.io.sigmf_loader import SigMFSignalLoader
                    rec = SigMFSignalLoader().load(f)
                else:
                    continue

                feat = FeatureExtractor.extract_all(rec)
                X_list.append(feat.ml_feature_vector)
                y_list.append(mod_idx)
            except Exception as e:
                print(f"      [!] Warning: Failed to extract features from {f.name}: {e}")

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y, classes


def load_from_radioml(
    radioml_path: Path,
    min_snr: float = 0.0,
    target_modulations: Optional[List[str]] = None,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads and extracts features from DeepSig RadioML 2016.10a dictionary pickle file.
    Dictionary format: {(mod_str, snr_int): ndarray of shape (N, 2, 128)}
    """
    radioml_path = Path(radioml_path)
    if not radioml_path.exists():
        raise FileNotFoundError(f"RadioML file not found: {radioml_path}")

    print(f"[*] Unpickling RadioML dataset from {radioml_path}...")
    with open(radioml_path, "rb") as f:
        # Compatible with both Python 2 and Python 3 pickle
        data = pickle.load(f, encoding="latin1")

    # Map RadioML names to SignalInsight standard modulation names
    rml_map = {
        "BPSK": MOD_BPSK,
        "QPSK": MOD_QPSK,
        "8PSK": MOD_8PSK,
        "QAM16": MOD_16QAM,
        "16QAM": MOD_16QAM,
        "CPFSK": MOD_FSK,
        "GFSK": MOD_FSK,
    }

    if target_modulations is None:
        target_modulations = list(SUPPORTED_MODULATIONS)

    classes = target_modulations
    class_to_idx = {c: i for i, c in enumerate(classes)}

    X_list = []
    y_list = []

    print(f"[*] Filtering and extracting features (SNR >= {min_snr} dB)...")
    for (mod_name, snr), frames in data.items():
        standard_mod = rml_map.get(mod_name.upper())
        if standard_mod not in class_to_idx:
            continue
        if snr < min_snr:
            continue

        mod_idx = class_to_idx[standard_mod]
        # frames shape is typically (N, 2, 128)
        for i in range(len(frames)):
            frame = frames[i]
            # frame[0] is I, frame[1] is Q
            iq_complex = (frame[0] + 1j * frame[1]).astype(np.complex64)

            rec = SignalRecord(
                samples=iq_complex,
                sample_rate=1_000_000.0,
                center_frequency=0.0,
                timestamp=datetime.utcnow(),
                data_type="complex64",
                channels=2,
                iq_order="IQ",
            )
            feat = FeatureExtractor.extract_all(rec)
            X_list.append(feat.ml_feature_vector)
            y_list.append(mod_idx)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y, classes


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    classes: List[str],
    output_model_path: Path,
    n_estimators: int = 120,
    max_depth: int = 5,
    learning_rate: float = 0.1,
    test_size: float = 0.2,
    seed: int = 42,
) -> None:
    """Trains an XGBoost classifier, evaluates on held-out test data, and saves to file."""
    print(f"[*] Total dataset size: {X.shape[0]} samples with {X.shape[1]} features each.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )
    print(f"[*] Split: {len(X_train)} training samples, {len(X_test)} validation samples.")

    print(f"[*] Training XGBClassifier (trees={n_estimators}, depth={max_depth}, lr={learning_rate})...")
    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    print("\n" + "=" * 60)
    print("           MODEL EVALUATION & METRICS REPORT")
    print("=" * 60)
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=classes, digits=4)
    print(report)

    # Confusion Matrix
    print("CONFUSION MATRIX:")
    cm = confusion_matrix(y_test, y_pred)
    header = "          " + "".join(f"{c:>9}" for c in classes)
    print(header)
    for idx, row in enumerate(cm):
        row_str = f"{classes[idx]:>9} " + "".join(f"{val:>9}" for val in row)
        print(row_str)
    print("=" * 60 + "\n")

    # Save
    output_model_path = Path(output_model_path)
    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(output_model_path))
    print(f"[SUCCESS] Model successfully serialized and saved to: {output_model_path.resolve()}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SignalInsight Automatic Modulation Classification (AMC) Model Trainer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["synthetic", "directory", "radioml"],
        default="synthetic",
        help="Dataset source mode: 'synthetic' (built-in DSP generator), 'directory' (folders of .wav/.iq), or 'radioml' (pickle)",
    )
    parser.add_argument(
        "--samples-per-class",
        type=int,
        default=200,
        help="Number of synthetic samples per class (only used with --mode synthetic)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/datasets",
        help="Directory path containing class folders (only used with --mode directory)",
    )
    parser.add_argument(
        "--radioml-file",
        type=str,
        default="data/RML2016.10a_dict.pkl",
        help="Path to RadioML dictionary .pkl file (only used with --mode radioml)",
    )
    parser.add_argument(
        "--min-snr",
        type=float,
        default=0.0,
        help="Minimum SNR (dB) threshold when loading RadioML or synthetic",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).parent / "models" / "amc_xgboost_v1.json"),
        help="Output model path where serialized XGBoost model will be saved",
    )
    parser.add_argument(
        "--trees",
        type=int,
        default=120,
        help="Number of boosting trees (n_estimators)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Maximum tree depth",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    if args.mode == "synthetic":
        X, y, classes = load_from_synthetic(
            num_samples_per_class=args.samples_per_class,
            snr_range=(args.min_snr, 30.0),
            seed=args.seed,
        )
    elif args.mode == "directory":
        X, y, classes = load_from_directory(Path(args.data_dir))
    elif args.mode == "radioml":
        X, y, classes = load_from_radioml(
            radioml_path=Path(args.radioml_file),
            min_snr=args.min_snr,
        )
    else:
        raise ValueError(f"Unknown mode: {args.mode}")

    train_model(
        X=X,
        y=y,
        classes=classes,
        output_model_path=Path(args.output),
        n_estimators=args.trees,
        max_depth=args.depth,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

