"""Base interfaces for carrier and symbol timing synchronization."""

from abc import ABC, abstractmethod
from typing import Any, Tuple
import numpy as np

from signalinsight.core.models import SignalRecord, SynchronizationResult


class BaseSynchronizer(ABC):
    """Abstract interface for waveform synchronization algorithms."""

    @abstractmethod
    def synchronize(
        self,
        signal_rec: SignalRecord,
        symbol_rate: float,
        **kwargs: Any,
    ) -> Tuple[SignalRecord, SynchronizationResult]:
        """Performs synchronization and returns synchronized signal and convergence metrics."""
        pass
