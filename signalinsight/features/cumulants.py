"""Higher-Order Cumulant (HOC) features with rigorous mathematical validation."""

from typing import Dict, NamedTuple
import numpy as np
from scipy import stats

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel


class CumulantsResult(NamedTuple):
    c20: complex
    c21: float
    c40: complex
    c41: complex
    c42: float
    f40: float
    f41: float
    f42: float
    feature_dict: Dict[str, ParameterValue]


class CumulantsCalculator:
    """
    Computes mathematically rigorous 2nd and 4th order cumulants of zero-mean complex signals.

    Definitions for zero-mean complex baseband signal x:
      C20 = E[x^2]
      C21 = E[|x|^2]
      C40 = E[x^4] - 3 * (C20)^2
      C41 = E[x^3 * conj(x)] - 3 * C20 * C21
      C42 = E[|x|^4] - |C20|^2 - 2 * (C21)^2

    Normalized invariants:
      f40 = |C40| / C21^2
      f41 = |C41| / C21^2
      f42 = |C42| / C21^2
    """

    @classmethod
    def compute(cls, samples: np.ndarray) -> CumulantsResult:
        if len(samples) < 32:
            raise ValueError("At least 32 samples required for reliable cumulant estimation.")

        # Zero-mean normalization
        x = samples - np.mean(samples)
        n = len(x)

        # Second-order moments
        # E[x^2]
        c20 = complex(np.mean(x ** 2))
        # E[|x|^2]
        c21 = float(np.mean(np.abs(x) ** 2))

        if c21 < 1e-12:
            c21 = 1e-12

        # Fourth-order moments
        # E[x^4]
        m40 = complex(np.mean(x ** 4))
        # E[x^3 * conj(x)]
        m41 = complex(np.mean((x ** 3) * np.conj(x)))
        # E[|x|^4]
        m42 = float(np.mean(np.abs(x) ** 4))

        # Cumulants
        c40 = m40 - 3.0 * (c20 ** 2)
        c41 = m41 - 3.0 * c20 * c21
        c42 = m42 - (abs(c20) ** 2) - 2.0 * (c21 ** 2)

        # Normalized invariants
        denom = c21 ** 2
        f40 = float(abs(c40) / denom)
        f41 = float(abs(c41) / denom)
        f42 = float(abs(c42) / denom)

        features = {
            "C20_mag": ParameterValue(
                name="|C20|",
                value=float(abs(c20)),
                unit="rel",
                source=ProvenanceSource.CALCULATED,
                method="|E[x^2]|",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "C21": ParameterValue(
                name="C21 (Variance)",
                value=float(c21),
                unit="rel",
                source=ProvenanceSource.CALCULATED,
                method="E[|x|^2]",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "C40_mag": ParameterValue(
                name="|C40|",
                value=float(abs(c40)),
                unit="rel",
                source=ProvenanceSource.CALCULATED,
                method="|E[x^4] - 3(E[x^2])^2|",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "C41_mag": ParameterValue(
                name="|C41|",
                value=float(abs(c41)),
                unit="rel",
                source=ProvenanceSource.CALCULATED,
                method="|E[x^3 x*] - 3 C20 C21|",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "C42": ParameterValue(
                name="C42",
                value=float(c42),
                unit="rel",
                source=ProvenanceSource.CALCULATED,
                method="E[|x|^4] - |C20|^2 - 2 C21^2",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "f40": ParameterValue(
                name="Normalized Cumulant f40",
                value=f40,
                unit="invariant",
                source=ProvenanceSource.CALCULATED,
                method="|C40| / C21^2",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "f41": ParameterValue(
                name="Normalized Cumulant f41",
                value=f41,
                unit="invariant",
                source=ProvenanceSource.CALCULATED,
                method="|C41| / C21^2",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
            "f42": ParameterValue(
                name="Normalized Cumulant f42",
                value=f42,
                unit="invariant",
                source=ProvenanceSource.CALCULATED,
                method="|C42| / C21^2",
                confidence=1.0,
                quality=QualityLevel.HIGH,
            ),
        }

        return CumulantsResult(
            c20=c20,
            c21=c21,
            c40=c40,
            c41=c41,
            c42=c42,
            f40=f40,
            f41=f41,
            f42=f42,
            feature_dict=features,
        )
