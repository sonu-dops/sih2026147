"""About and diagnostics dialog for SignalInsight."""

import os
import sys
from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget
import scipy
import xgboost as xgb

from signalinsight.core.constants import APP_NAME, APP_SUBTITLE, APP_VERSION, COLOR_PRIMARY_ACCENT


class AboutDialog(QDialog):
    """About dialog with system diagnostics and runtime specifications."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.resize(520, 420)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header Title
        lbl_title = QLabel(APP_NAME)
        lbl_title.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {COLOR_PRIMARY_ACCENT};")
        lbl_sub = QLabel(APP_SUBTITLE)
        lbl_sub.setStyleSheet("font-size: 9pt; color: #64748b;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)

        # System Diagnostics Text Box
        diag_info = [
            f"Software Version: {APP_VERSION}",
            f"Python Runtime: {sys.version.split()[0]} ({sys.platform})",
            f"NumPy Version: {np.__version__}",
            f"SciPy Version: {scipy.__version__}",
            f"XGBoost Version: {xgb.__version__}",
            f"PyQtGraph Version: {pg.__version__}",
            f"CPU Logical Cores: {os.cpu_count()}",
            "DSP Engine: Online (Vectorized 64-bit / Analytic Hilbert)",
            "AMC Engine: Online (XGBoost Invariant Decision Trees)",
            "SigMF Spec Support: v1.0.0 Compliant",
            "Report Generator: ReportLab Multi-Page Vector PDF",
            "",
            "Notice:",
            "SignalInsight is an engineering analysis workstation.",
            "All parameters display complete scientific provenance tags.",
            "Arbitrary blind decoding of unknown communications is strictly forbidden.",
        ]

        txt_diag = QTextEdit()
        txt_diag.setReadOnly(True)
        txt_diag.setPlainText("\n".join(diag_info))
        txt_diag.setStyleSheet(
            "background-color: #ffffff; color: #0f172a; font-family: monospace; font-size: 8.5pt; border: 1px solid #cbd5e1;"
        )
        layout.addWidget(txt_diag)

        btn_row = QHBoxLayout()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)
