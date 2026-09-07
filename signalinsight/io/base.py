"""Abstract base class for signal file loaders."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
from signalinsight.core.models import SignalRecord


class SignalLoader(ABC):
    """Abstract interface for ingesting RF signal files."""

    @abstractmethod
    def can_load(self, filepath: Path) -> bool:
        """Check if this loader supports the specified file."""
        pass

    @abstractmethod
    def inspect_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Inspect file header/metadata without reading full sample array."""
        pass

    @abstractmethod
    def load(
        self,
        filepath: Path,
        sample_rate: Optional[float] = None,
        center_frequency: Optional[float] = None,
        max_samples: Optional[int] = None,
        offset_samples: int = 0,
        **kwargs: Any,
    ) -> SignalRecord:
        """Load samples into a standardized SignalRecord."""
        pass
