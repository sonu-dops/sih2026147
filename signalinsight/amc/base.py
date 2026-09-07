"""Abstract base class for Automatic Modulation Classification (AMC)."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import numpy as np

from signalinsight.core.models import ModulationResult, SignalRecord


class BaseModulationClassifier(ABC):
    """Abstract interface for all modulation classification models."""

    @abstractmethod
    def predict(
        self,
        signal_rec: SignalRecord,
        confidence_threshold: Optional[float] = None,
    ) -> ModulationResult:
        """Classify modulation scheme from a SignalRecord."""
        pass

    @abstractmethod
    def predict_features(
        self,
        feature_vector: np.ndarray,
        confidence_threshold: Optional[float] = None,
    ) -> ModulationResult:
        """Classify modulation scheme directly from a feature vector."""
        pass

    @abstractmethod
    def get_supported_classes(self) -> List[str]:
        """Return list of modulation classes this classifier can detect."""
        pass
