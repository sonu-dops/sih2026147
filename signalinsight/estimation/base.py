"""Abstract base class for parameter estimators."""

from abc import ABC, abstractmethod
from typing import Any
from signalinsight.core.models import ParameterValue, SignalRecord


class ParameterEstimator(ABC):
    """Base interface for all scientific parameter estimators."""

    @abstractmethod
    def estimate(self, signal_rec: SignalRecord, **kwargs: Any) -> Any:
        """Estimates parameters and returns structured values with provenance."""
        pass
