"""Batch Analysis Dialog for multi-signal batch processing."""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.logging import logger
from signalinsight.core.models import AnalysisResult, SignalRecord
from signalinsight.io.wav_loader import WavSignalLoader
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner


class BatchRunnerThread(QThread):
    """Executes batch processing across a list of files."""

    item_finished = pyqtSignal(int, object)  # index, AnalysisResult
    batch_finished = pyqtSignal()

    def __init__(self, filepaths: List[Path], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.filepaths = filepaths
        self.runner = PipelineRunner()

    def run(self) -> None:
        loader = WavSignalLoader()
        for idx, fp in enumerate(self.filepaths):
            try:
                rec = loader.load(fp)
                res = self.runner.run(rec, options=PipelineOptions())
                self.item_finished.emit(idx, res)
            except Exception as e:
                logger.error("Batch", f"Failed to process {fp.name}: {e}")
        self.batch_finished.emit()


class BatchProcessorDialog(QDialog):
    """Batch Processor dialog for analyzing multiple recordings simultaneously."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.filepaths: List[Path] = []
        self.setWindowTitle("Batch Signal Analysis")
        self.resize(850, 480)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Top Bar
        bar_layout = QHBoxLayout()
        btn_add = QPushButton("Add Files...")
        btn_add.clicked.connect(self._add_files)

        self.btn_run = QPushButton("Start Batch Processing")
        self.btn_run.setObjectName("primary_action")
        self.btn_run.clicked.connect(self._start_batch)

        bar_layout.addWidget(btn_add)
        bar_layout.addWidget(self.btn_run)
        bar_layout.addStretch()
        layout.addLayout(bar_layout)

        # Summary Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["File", "Modulation", "Confidence", "Carrier Freq", "Symbol Rate", "99% OBW", "SNR", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def _add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select Signal Files", "", "Signal Files (*.wav *.iq *.sigmf-meta)")
        for f in files:
            p = Path(f)
            self.filepaths.append(p)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            for c in range(1, 7):
                self.table.setItem(row, c, QTableWidgetItem("--"))
            self.table.setItem(row, 7, QTableWidgetItem("Queued"))

    def _start_batch(self) -> None:
        if not self.filepaths:
            return
        self.btn_run.setEnabled(False)
        self.thread = BatchRunnerThread(self.filepaths, self)
        self.thread.item_finished.connect(self._on_item_finished)
        self.thread.batch_finished.connect(self._on_batch_finished)
        self.thread.start()

    def _on_item_finished(self, idx: int, res: AnalysisResult) -> None:
        mod = res.modulation_result.predicted_modulation if res.modulation_result else "N/A"
        conf = f"{res.modulation_result.confidence*100:.1f}%" if res.modulation_result else "N/A"
        cf = f"{res.carrier_frequency.value:,.1f} Hz" if res.carrier_frequency.value is not None else "N/A"
        sr = f"{res.symbol_rate.value:,.1f} Baud" if res.symbol_rate.value is not None else "N/A"
        obw = f"{res.occupied_bw_99.value:,.1f} Hz" if res.occupied_bw_99.value is not None else "N/A"
        snr = f"{res.snr_db.value:.2f} dB" if res.snr_db.value is not None else "N/A"

        self.table.setItem(idx, 1, QTableWidgetItem(mod))
        self.table.setItem(idx, 2, QTableWidgetItem(conf))
        self.table.setItem(idx, 3, QTableWidgetItem(cf))
        self.table.setItem(idx, 4, QTableWidgetItem(sr))
        self.table.setItem(idx, 5, QTableWidgetItem(obw))
        self.table.setItem(idx, 6, QTableWidgetItem(snr))
        self.table.setItem(idx, 7, QTableWidgetItem("Completed"))

        pct = int(((idx + 1) / len(self.filepaths)) * 100)
        self.progress_bar.setValue(pct)

    def _on_batch_finished(self) -> None:
        self.btn_run.setEnabled(True)
        self.progress_bar.setValue(100)
