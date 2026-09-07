"""Preferences and application settings dialog."""

from typing import Optional
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.config import config


class SettingsDialog(QDialog):
    """Application preferences dialog."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Preferences & Hardware Configuration")
        self.resize(500, 380)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Tab 1: Processing
        tab_proc = QWidget()
        form_proc = QFormLayout(tab_proc)
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 32)
        self.spin_workers.setValue(config.processing.max_cpu_workers)
        form_proc.addRow("CPU Workers:", self.spin_workers)

        self.chk_gpu = QCheckBox("Enable GPU Acceleration (if supported)")
        self.chk_gpu.setChecked(config.processing.enable_gpu)
        form_proc.addRow("GPU Acceleration:", self.chk_gpu)

        self.spin_chunk = QSpinBox()
        self.spin_chunk.setRange(10000, 100000000)
        self.spin_chunk.setValue(config.processing.chunk_size_samples)
        form_proc.addRow("Processing Chunk Size (samples):", self.spin_chunk)
        tabs.addTab(tab_proc, "Processing")

        # Tab 2: Classification
        tab_amc = QWidget()
        form_amc = QFormLayout(tab_amc)
        self.spin_thresh = QDoubleSpinBox()
        self.spin_thresh.setRange(0.1, 0.99)
        self.spin_thresh.setValue(config.classification.confidence_threshold)
        self.spin_thresh.setSingleStep(0.05)
        form_amc.addRow("Confidence Rejection Threshold:", self.spin_thresh)
        tabs.addTab(tab_amc, "Classification")

        # Tab 3: Reports
        tab_rep = QWidget()
        form_rep = QFormLayout(tab_rep)
        self.txt_org = QLineEdit(config.reports.organization)
        form_rep.addRow("Organization / Laboratory:", self.txt_org)
        self.txt_analyst = QLineEdit(config.reports.analyst_name)
        form_rep.addRow("Lead Analyst:", self.txt_analyst)
        tabs.addTab(tab_rep, "Reports")

        layout.addWidget(tabs)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Preferences")
        btn_save.setObjectName("primary_action")
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _save(self) -> None:
        config.processing.max_cpu_workers = self.spin_workers.value()
        config.processing.enable_gpu = self.chk_gpu.isChecked()
        config.processing.chunk_size_samples = self.spin_chunk.value()
        config.classification.confidence_threshold = self.spin_thresh.value()
        config.reports.organization = self.txt_org.text()
        config.reports.analyst_name = self.txt_analyst.text()
        self.accept()
