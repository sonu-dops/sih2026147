"""I/Q statistical moments, cross-correlation, and quadrature imbalance features."""

from typing import Dict
import numpy as np

from signalinsight.core.models import ParameterValue, ProvenanceSource, QualityLevel


class IQFeaturesCalculator:
    """Computes I/Q balance, covariance, and quadrature orthogonality metrics."""

    @staticmethod
    def compute(samples: np.ndarray) -> Dict[str, ParameterValue]:
        if not np.iscomplexobj(samples):
            return {}

        i_vals = samples.real
        q_vals = samples.imag

        i_var = float(np.var(i_vals))
        q_var = float(np.var(q_vals))
        i_std = float(np.std(i_vals))
        q_std = float(np.std(q_vals))

        # Covariance and correlation coefficient
        cov_matrix = np.cov(i_vals, q_vals)
        cov_iq = float(cov_matrix[0, 1]) if cov_matrix.shape == (2, 2) else 0.0

        denom = max(1e-12, i_std * q_std)
        rho_iq = float(cov_iq / denom)

        # IQ Amplitude Imbalance in dB: 10*log10(Var(I) / Var(Q))
        iq_gain_imbalance_db = float(10.0 * np.log10(max(1e-6, i_var / max(1e-12, q_var))))

        # Quadrature phase error (degrees): arcsin(rho)
        safe_rho = np.clip(rho_iq, -0.999, 0.999)
        quadrature_skew_deg = float(np.degrees(np.arcsin(safe_rho)))

        def _p(name: str, val: float, unit: str, method: str) -> ParameterValue:
            return ParameterValue(
                name=name,
                value=val,
                unit=unit,
                source=ProvenanceSource.CALCULATED,
                method=method,
                confidence=1.0,
                quality=QualityLevel.HIGH,
            )

        return {
            "i_variance": _p("I Variance", i_var, "V^2", "Var(I)"),
            "q_variance": _p("Q Variance", q_var, "V^2", "Var(Q)"),
            "iq_covariance": _p("I/Q Covariance", cov_iq, "V^2", "Cov(I, Q)"),
            "iq_correlation": _p("I/Q Correlation Coefficient", rho_iq, "ratio", "Cov(I, Q) / (std(I)*std(Q))"),
            "iq_amplitude_imbalance_db": _p("IQ Amplitude Imbalance", iq_gain_imbalance_db, "dB", "10*log10(Var(I)/Var(Q))"),
            "quadrature_skew_deg": _p("Quadrature Phase Skew", quadrature_skew_deg, "deg", "arcsin(rho_IQ)"),
        }
