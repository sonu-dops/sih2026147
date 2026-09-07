"""Synchronization subsystem: carrier sync, timing sync, and matched filtering."""

from signalinsight.synchronization.base import BaseSynchronizer
from signalinsight.synchronization.carrier_sync import CarrierSynchronizer, CostasLoop, CostasLoopResult
from signalinsight.synchronization.timing_sync import GardnerTimingRecovery, TimingRecoveryResult
from signalinsight.synchronization.matched_filter import MatchedFilterProcessor

__all__ = [
    "BaseSynchronizer",
    "CarrierSynchronizer",
    "CostasLoop",
    "CostasLoopResult",
    "GardnerTimingRecovery",
    "TimingRecoveryResult",
    "MatchedFilterProcessor",
]
