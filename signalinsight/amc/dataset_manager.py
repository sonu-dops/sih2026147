"""Dataset manager for downloading and extracting RadioML 2016.10a benchmark datasets."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile
from typing import Optional

from signalinsight.core.logging import logger


class RadioMLDatasetManager:
    """Manages the download, extraction, and file location for RadioML 2016.10a."""

    DATASET_SLUG = "pinxau1000/radioml201610a"
    DEFAULT_STORAGE_DIR = Path("data/datasets")
    PKL_FILENAME = "RML2016.10a_dict.pkl"

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = Path(target_dir) if target_dir else self.DEFAULT_STORAGE_DIR
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def find_dataset_file(self) -> Optional[Path]:
        """Searches common project directories for the extracted RadioML pickle file."""
        candidates = [
            self.target_dir / self.PKL_FILENAME,
            Path("data") / self.PKL_FILENAME,
            self.target_dir / "radioml201610a" / self.PKL_FILENAME,
            Path("samples") / self.PKL_FILENAME,
        ]
        for c in candidates:
            if c.exists() and c.stat().st_size > 0:
                return c

        # Search recursively inside target_dir for any matching .pkl
        for p in self.target_dir.rglob("*.pkl"):
            if "rml2016" in p.name.lower() or "radioml" in p.name.lower() or "2016.10a" in p.name.lower():
                return p
        return None

    def extract_archives(self) -> Optional[Path]:
        """Extracts any found zip or tar.bz2 archives in target_dir."""
        # Check for zip
        for z in list(self.target_dir.glob("*.zip")) + list(Path("data").glob("*.zip")):
            logger.info("Dataset", f"Found zip archive: {z.name}. Extracting...")
            try:
                with zipfile.ZipFile(z, "r") as zip_ref:
                    zip_ref.extractall(self.target_dir)
                found = self.find_dataset_file()
                if found:
                    logger.info("Dataset", f"Extracted dataset pickle: {found}")
                    return found
            except Exception as e:
                logger.error("Dataset", f"Failed extracting {z.name}: {e}")

        # Check for tar.bz2
        for t in list(self.target_dir.glob("*.tar.bz2")) + list(Path("data").glob("*.tar.bz2")):
            logger.info("Dataset", f"Found tar.bz2 archive: {t.name}. Extracting...")
            try:
                with tarfile.open(t, "r:bz2") as tar_ref:
                    tar_ref.extractall(self.target_dir)
                found = self.find_dataset_file()
                if found:
                    logger.info("Dataset", f"Extracted dataset pickle: {found}")
                    return found
            except Exception as e:
                logger.error("Dataset", f"Failed extracting {t.name}: {e}")

        return self.find_dataset_file()

    def has_kaggle_auth(self) -> bool:
        """Checks whether Kaggle credentials exist via file or environment variables."""
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        if kaggle_json.exists():
            return True
        if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
            return True
        return False

    def download_via_kaggle(self) -> Optional[Path]:
        """Invokes the Kaggle CLI to download and unzip pinxau1000/radioml201610a."""
        existing = self.find_dataset_file()
        if existing:
            return existing

        # First check archives
        extracted = self.extract_archives()
        if extracted:
            return extracted

        if not self.has_kaggle_auth():
            logger.warning(
                "Dataset",
                "Kaggle credentials not detected. Place kaggle.json in ~/.kaggle/ or set KAGGLE_USERNAME / KAGGLE_KEY."
            )
            return None

        logger.info("Dataset", f"Running kaggle datasets download for {self.DATASET_SLUG}...")
        cmd = [
            sys.executable,
            "-m",
            "kaggle",
            "datasets",
            "download",
            "-d",
            self.DATASET_SLUG,
            "-p",
            str(self.target_dir),
            "--unzip",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Dataset", f"Kaggle download output:\n{res.stdout}")
            return self.extract_archives() or self.find_dataset_file()
        except subprocess.CalledProcessError as e:
            logger.error("Dataset", f"Kaggle download failed:\n{e.stderr or e.stdout}")
            return None


if __name__ == "__main__":
    mgr = RadioMLDatasetManager()
    found = mgr.find_dataset_file()
    if found:
        print(f"[SUCCESS] Found RadioML dataset: {found}")
    else:
        print("[*] Attempting Kaggle download...")
        res = mgr.download_via_kaggle()
        if res:
            print(f"[SUCCESS] Downloaded and extracted dataset to: {res}")
        else:
            print("[!] Could not download automatically. Please provide Kaggle credentials or dataset file.")
