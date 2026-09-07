"""Structured JSON export of analysis results and provenance metadata."""

from pathlib import Path
from typing import Any, Dict
from signalinsight.core.models import AnalysisResult


class JSONExporter:
    """Exports AnalysisResult to a standardized JSON schema."""

    @staticmethod
    def export(result: AnalysisResult, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
