"""SignalInsight Backend Configuration."""

from pathlib import Path
from typing import List, Union
import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./data/signalinsight.db"

    # API Server
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # File Storage Paths
    file_storage_path: Path = Path("./data/signals")
    dataset_storage_path: Path = Path("./data/datasets")
    model_storage_path: Path = Path("./data/models")
    report_storage_path: Path = Path("./data/reports")
    cache_path: Path = Path("./data/cache")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def init_storage_dirs(self) -> None:
        """Ensures all configured storage directories exist on disk."""
        for p in [
            self.file_storage_path,
            self.dataset_storage_path,
            self.model_storage_path,
            self.report_storage_path,
            self.cache_path,
        ]:
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
