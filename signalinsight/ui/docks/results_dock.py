"""Results Summary dock displaying compact laboratory measurements."""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import COLOR_PRIMARY_ACCENT, COLOR_SUCCESS, COLOR_TEXT_MUTED, COLOR_WARNING
from signalinsight.core.models import AnalysisResult


class ResultsSummaryDock(QDockWidget):
    """Compact laboratory instrument results summary."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("RESULTS SUMMARY", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self._init_ui()

    def _init_ui(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Modulation Banner Card
        self.banner = QFrame()
        self.banner.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px;")
        banner_layout = QVBoxLayout(self.banner)
        banner_layout.setSpacing(2)

        lbl_title = QLabel("DETECTED MODULATION")
        lbl_title.setStyleSheet("color: #64748b; font-size: 8pt; font-weight: bold; letter-spacing: 0.5px;")

        self.lbl_mod_class = QLabel("UNCERTAIN")
        self.lbl_mod_class.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 18pt; font-weight: bold;")

        self.lbl_confidence = QLabel("Confidence: -- %")
        self.lbl_confidence.setStyleSheet("color: #334155; font-size: 9pt; font-weight: 500;")

        banner_layout.addWidget(lbl_title)
        banner_layout.addWidget(self.lbl_mod_class)
        banner_layout.addWidget(self.lbl_confidence)
        layout.addWidget(self.banner)

        # Results Table
        self.table = QTableWidget(9, 2)
        self.table.setHorizontalHeaderLabels(["Measurement", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        rows = [
            "Carrier Frequency",
            "Carrier Offset",
            "Symbol Rate",
            "99% Occupied BW",
            "-3 dB Bandwidth",
            "SNR",
            "EVM RMS",
            "Synchronization",
            "Decoding Status",
        ]
        for idx, name in enumerate(rows):
            self.table.setItem(idx, 0, QTableWidgetItem(name))
            self.table.setItem(idx, 1, QTableWidgetItem("N/A"))

        layout.addWidget(self.table)
        self.setWidget(content)

    def set_result(self, result: AnalysisResult) -> None:
        if result.modulation_result:
            mod = result.modulation_result.predicted_modulation
            conf = result.modulation_result.confidence * 100.0
            self.lbl_mod_class.setText(mod)
            color = COLOR_SUCCESS if conf >= 75.0 else (COLOR_WARNING if conf >= 50.0 else "#ff3366")
            self.lbl_mod_class.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")
            self.lbl_confidence.setText(f"Confidence: {conf:.1f}% [{result.modulation_result.model_name}]")
        else:
            self.lbl_mod_class.setText("N/A")
            self.lbl_confidence.setText("Confidence: N/A")

        cf_val = result.carrier_frequency.display_str()
        cfo_val = result.carrier_offset.display_str()
        sr_val = result.symbol_rate.display_str()
        obw_val = result.occupied_bw_99.display_str()
        bw3_val = result.bandwidth_3db.display_str()
        snr_val = result.snr_db.display_str()

        evm_val = "N/A"
        if result.demodulation_result and result.demodulation_result.evm_rms_pct:
            evm_val = result.demodulation_result.evm_rms_pct.display_str()

        sync_val = "Converged" if (result.synchronization_result and result.synchronization_result.converged) else "Unlocked / Bypass"
        dec_val = result.decoding_result.message if result.decoding_result else "Not configured"

        row_vals = [cf_val, cfo_val, sr_val, obw_val, bw3_val, snr_val, evm_val, sync_val, dec_val]
        for idx, val in enumerate(row_vals):
            self.table.setItem(idx, 1, QTableWidgetItem(val))
