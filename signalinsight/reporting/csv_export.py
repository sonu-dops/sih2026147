"""Tabular CSV export for signal parameters and extracted features."""

import csv
from pathlib import Path
from signalinsight.core.models import AnalysisResult, ParameterValue


class CSVExporter:
    """Exports signal parameters and features to a flat tabular CSV file."""

    @staticmethod
    def export(result: AnalysisResult, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rows = []

        def add_param(p: ParameterValue, category: str):
            rows.append(
                {
                    "Category": category,
                    "Parameter": p.name,
                    "Value": str(p.value) if p.value is not None else "N/A",
                    "Unit": p.unit,
                    "Provenance": p.source.value,
                    "Quality": p.quality.value,
                    "Confidence": f"{p.confidence * 100:.1f}%",
                    "Method": p.method,
                    "Notes": p.notes or "",
                }
            )

        # File and basic RF parameters
        add_param(result.sample_rate, "Metadata")
        add_param(result.center_frequency, "Metadata")
        add_param(result.carrier_frequency, "RF Parameters")
        add_param(result.carrier_offset, "RF Parameters")
        add_param(result.symbol_rate, "RF Parameters")
        add_param(result.occupied_bw_99, "Spectral")
        add_param(result.bandwidth_3db, "Spectral")
        add_param(result.snr_db, "Power & Noise")
        add_param(result.signal_power, "Power & Noise")
        add_param(result.noise_floor, "Power & Noise")
        add_param(result.dc_offset_i, "DC Offset")
        add_param(result.dc_offset_q, "DC Offset")

        # Cumulant features
        for key, p in result.cumulants.items():
            add_param(p, "Higher-Order Cumulants")

        # General features
        for key, p in result.features.items():
            add_param(p, "Extracted Features")

        # Constellation / Demod metrics
        if result.demodulation_result and result.demodulation_result.evm_rms_pct:
            add_param(result.demodulation_result.evm_rms_pct, "Constellation")

        fieldnames = [
            "Category",
            "Parameter",
            "Value",
            "Unit",
            "Provenance",
            "Quality",
            "Confidence",
            "Method",
            "Notes",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
