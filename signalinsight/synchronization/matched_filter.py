"""Matched filtering subsystem for pulse shape filtering."""

from signalinsight.dsp.filters import FilterEngine, PulseShape
from signalinsight.core.models import SignalRecord


class MatchedFilterProcessor:
    """Convenience wrapper for applying RRC/RC matched filters."""

    @staticmethod
    def process(
        signal_rec: SignalRecord,
        samples_per_symbol: int = 4,
        beta: float = 0.35,
        span_symbols: int = 8,
    ) -> SignalRecord:
        return FilterEngine.apply_matched_filter(
            signal_rec,
            pulse_shape=PulseShape.ROOT_RAISED_COSINE,
            samples_per_symbol=samples_per_symbol,
            beta=beta,
            span_symbols=span_symbols,
        )
