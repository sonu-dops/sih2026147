"""SignalInsight application entry point with GUI and CLI support."""

import argparse
from pathlib import Path
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from signalinsight.core.constants import APP_NAME, APP_SUBTITLE, APP_VERSION
from signalinsight.core.logging import logger
from signalinsight.io.iq_loader import RawIQSignalLoader
from signalinsight.io.sigmf_loader import SigMFSignalLoader
from signalinsight.io.wav_loader import WavSignalLoader
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner
from signalinsight.reporting.pdf_report import PDFReportGenerator
from signalinsight.ui.app import MainWindow


def run_cli_analysis(filepath: Path, output_pdf: Path) -> int:
    """Executes headless analysis pipeline and generates PDF report directly."""
    filepath = Path(filepath)
    output_pdf = Path(output_pdf)
    logger.info("CLI", f"Running headless analysis on: {filepath}")

    ext = filepath.suffix.lower()
    if ext == ".wav":
        loader = WavSignalLoader()
    elif ext in (".sigmf-meta", ".sigmf-data"):
        loader = SigMFSignalLoader()
    else:
        loader = RawIQSignalLoader()

    rec = loader.load(filepath)
    runner = PipelineRunner()
    result = runner.run(rec, options=PipelineOptions())

    PDFReportGenerator.generate(result, output_pdf)
    logger.info("CLI", f"Analysis complete. Report generated at: {output_pdf}")
    print(f"\n[SUCCESS] SignalInsight Report generated: {output_pdf}")
    if result.modulation_result:
        print(f"Detected Modulation: {result.modulation_result.predicted_modulation} ({result.modulation_result.confidence*100:.1f}%)")
    print(f"Carrier Frequency: {result.carrier_frequency.display_str()}")
    print(f"99% Occupied BW: {result.occupied_bw_99.display_str()}")
    print(f"Estimated SNR: {result.snr_db.display_str()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} — {APP_SUBTITLE}")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument("--file", "-f", type=str, help="Input signal file (.wav, .iq, .sigmf-meta)")
    parser.add_argument("--report", "-r", type=str, help="Generate PDF report headlessly and exit")

    args = parser.parse_args()

    if args.file and args.report:
        return run_cli_analysis(Path(args.file), Path(args.report))

    # Launch Desktop GUI
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow()

    if args.file:
        window._load_file_path(Path(args.file))

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
