"""Secure local filesystem storage manager."""

import hashlib
import os
from pathlib import Path
import re
import shutil
from typing import Tuple

from backend.app.config import settings


class FileStorageManager:
    """Handles secure file saving, path sanitization, and SHA-256 verification."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes filename against path traversal and dangerous characters."""
        # Strip path characters
        cleaned = os.path.basename(filename)
        # Remove any non-alphanumeric chars except dots, underscores, dashes
        cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", cleaned)
        if not cleaned or cleaned.startswith("."):
            cleaned = f"signal_{cleaned.lstrip('.')}"
        return cleaned

    @classmethod
    def save_uploaded_signal(cls, filename: str, content: bytes) -> Tuple[Path, str, int]:
        """
        Saves raw signal file content to the configured storage directory.
        Returns (target_path, sha256_hash, file_size_bytes).
        """
        settings.init_storage_dirs()
        safe_name = cls.sanitize_filename(filename)
        sha256 = hashlib.sha256(content).hexdigest()

        # Name with hash prefix to prevent collisions while preserving original name
        target_path = settings.file_storage_path / f"{sha256[:12]}_{safe_name}"
        with open(target_path, "wb") as f:
            f.write(content)

        return target_path, sha256, len(content)

    @classmethod
    def save_local_file_reference(cls, local_path: Path) -> Tuple[Path, str, int]:
        """
        Validates an existing local file, computes hash, and copies or registers it.
        """
        settings.init_storage_dirs()
        local_path = Path(local_path)
        if not local_path.exists() or not local_path.is_file():
            raise FileNotFoundError(f"Source signal file does not exist: {local_path}")

        safe_name = cls.sanitize_filename(local_path.name)
        with open(local_path, "rb") as f:
            sha256 = hashlib.sha256(f.read(65536)).hexdigest()
            f.seek(0, os.SEEK_END)
            size = f.tell()

        target_path = settings.file_storage_path / f"{sha256[:12]}_{safe_name}"
        if not target_path.exists():
            shutil.copy2(local_path, target_path)

        return target_path, sha256, size
