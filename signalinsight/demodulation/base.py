"""Base interface for digital demodulators."""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import numpy as np

from signalinsight.core.models import DemodulationResult


class BaseDemodulator(ABC):
    """Abstract demodulator interface."""

    @abstractmethod
    def demodulate(self, symbols: np.ndarray) -> DemodulationResult:
        """Demodulate symbol array into bits and constellation metrics."""
        pass

    @abstractmethod
    def get_ideal_constellation(self) -> np.ndarray:
        """Returns array of complex ideal constellation points."""
        pass

    @abstractmethod
    def get_symbol_mapping(self) -> Dict[int, complex]:
        """Returns mapping from integer symbol value to ideal complex IQ coordinate."""
        pass
