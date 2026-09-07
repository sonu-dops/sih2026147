"""Base interface for decoding and forward error correction (FEC)."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
from signalinsight.core.models import DecodingResult


class BaseDecoder(ABC):
    """Abstract decoder interface."""

    @abstractmethod
    def decode(self, bits: List[int], **kwargs: Any) -> DecodingResult:
        """Attempt to decode bitstream according to known framing and coding."""
        pass
