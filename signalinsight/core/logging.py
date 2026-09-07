"""Structured logging and audit trail system."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Callable, List, Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Structured log record for display and export."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module: str
    message: str
    session_id: str
    details: Optional[str] = None

    def formatted_line(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        return f"{time_str} [{self.level:<7}] [{self.module:<15}] {self.message}"


class AppLogger:
    """Central logging controller with Qt console hooks."""

    def __init__(self, name: str = "SignalInsight"):
        self.session_id: str = str(uuid.uuid4())[:8]
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Standard console handler
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%H:%M:%S",
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        self._entries: List[LogEntry] = []
        self._listeners: List[Callable[[LogEntry], None]] = []

    def add_listener(self, callback: Callable[[LogEntry], None]) -> None:
        self._listeners.append(callback)

    def log(self, level: int, module: str, message: str, details: Optional[str] = None):
        level_name = logging.getLevelName(level)
        entry = LogEntry(
            level=level_name,
            module=module,
            message=message,
            session_id=self.session_id,
            details=details,
        )
        self._entries.append(entry)
        self.logger.log(level, f"[{module}] {message}")
        for cb in self._listeners:
            try:
                cb(entry)
            except Exception:
                pass

    def debug(self, module: str, message: str, details: Optional[str] = None):
        self.log(logging.DEBUG, module, message, details)

    def info(self, module: str, message: str, details: Optional[str] = None):
        self.log(logging.INFO, module, message, details)

    def warning(self, module: str, message: str, details: Optional[str] = None):
        self.log(logging.WARNING, module, message, details)

    def error(self, module: str, message: str, details: Optional[str] = None):
        self.log(logging.ERROR, module, message, details)

    def critical(self, module: str, message: str, details: Optional[str] = None):
        self.log(logging.CRITICAL, module, message, details)

    def get_entries(self) -> List[LogEntry]:
        return list(self._entries)

    def clear(self):
        self._entries.clear()


# Global logger instance
logger = AppLogger()
