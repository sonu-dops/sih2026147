"""Application configuration and user preferences."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import json
import os


class GeneralConfig(BaseModel):
    theme: str = "light"
    autosave: bool = True
    autosave_interval_s: int = 300
    default_project_dir: str = str(Path.home() / "SignalInsight_Projects")


class ProcessingConfig(BaseModel):
    max_cpu_workers: int = Field(default_factory=lambda: max(1, os.cpu_count() or 4))
    enable_gpu: bool = False
    chunk_size_samples: int = 1_000_000
    cache_dir: str = str(Path.home() / ".signalinsight_cache")
    memory_limit_mb: int = 4096


class SignalDefaultsConfig(BaseModel):
    default_sample_rate: float = 10_000_000.0  # 10 Msps
    default_center_frequency: float = 0.0
    default_iq_format: str = "float32"
    default_iq_order: str = "IQ"
    default_window: str = "Hann"
    default_fft_size: int = 2048


class ClassificationConfig(BaseModel):
    model_type: str = "xgboost"  # "xgboost" or "random_forest"
    confidence_threshold: float = 0.65
    models_dir: str = str(Path(__file__).parent.parent / "amc" / "models")


class VisualizationConfig(BaseModel):
    enable_antialiasing: bool = True
    show_grid: bool = True
    max_scatter_points: int = 50000
    default_spectrogram_cmap: str = "viridis"
    waterfall_history_slices: int = 100


class ReportsConfig(BaseModel):
    organization: str = "SignalInsight RF Laboratory"
    analyst_name: str = "RF Engineer"
    default_report_dir: str = str(Path.home() / "SignalInsight_Reports")


class AppConfig(BaseModel):
    """Unified application configuration."""
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    signal: SignalDefaultsConfig = Field(default_factory=SignalDefaultsConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)

    def save(self, filepath: Path) -> None:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, filepath: Path) -> "AppConfig":
        filepath = Path(filepath)
        if not filepath.exists():
            return cls()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception:
            return cls()


# Default singleton instance
config = AppConfig()
