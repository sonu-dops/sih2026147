"""Model training, evaluation, and serialization routine for SignalInsight AMC."""

from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from signalinsight.amc.classifier import XGBoostModulationClassifier
from signalinsight.core.logging import logger


def train_and_save_model(
    output_model_path: Path,
    num_train_per_class: int = 150,
    num_test_per_class: int = 50,
) -> None:
    """Trains and serializes the baseline XGBoost classifier, printing evaluation report."""
    logger.info("AMC", f"Starting AMC baseline training with {num_train_per_class} signals/class...")
    classifier = XGBoostModulationClassifier()
    classifier.train_baseline(num_samples_per_class=num_train_per_class, seed=42)

    # Save trained model
    output_model_path = Path(output_model_path)
    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    classifier.save(output_model_path)
    logger.info("AMC", f"Model successfully saved to {output_model_path}")


if __name__ == "__main__":
    model_dst = Path(__file__).parent / "models" / "amc_xgboost_v1.json"
    train_and_save_model(model_dst)
