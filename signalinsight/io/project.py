"""Project management and persistence (.siproj)."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from signalinsight.core.models import Marker


class ProjectMetadata(BaseModel):
    name: str = "Untitled Project"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    author: str = "SignalInsight Engineer"
    description: str = ""
    app_version: str = "1.0.0"


class ProjectFile(BaseModel):
    """Container for saving and restoring SignalInsight analysis sessions."""
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    signal_files: List[str] = Field(default_factory=list)
    active_signal_file: Optional[str] = None
    markers: List[Marker] = Field(default_factory=list)
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    processing_presets: Dict[str, Any] = Field(default_factory=dict)


class ProjectManager:
    """Handles saving, loading, and serializing SignalInsight projects."""

    @staticmethod
    def save_project(project: ProjectFile, filepath: Path) -> None:
        filepath = Path(filepath)
        project.metadata.modified_at = datetime.utcnow()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(project.model_dump_json(indent=2))

    @staticmethod
    def load_project(filepath: Path) -> ProjectFile:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Project file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectFile(**data)
