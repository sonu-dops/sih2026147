"""Results Summary dock displaying compact laboratory measurements."""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

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
        self.table = QTableWidget(10, 2)
        self.table.setHorizontalHeaderLabels(["Measurement", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setMinimumHeight(250)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        rows = [
            "Carrier Frequency",
            "Carrier Offset",
            "Symbol Rate",
            "99% Occupied BW",
            "-3 dB Bandwidth",
            "SNR",
            "EVM RMS",
            "Demodulated Bits",
            "Channel Coding (FEC)",
            "Synchronization",
        ]
        for idx, name in enumerate(rows):
            self.table.setItem(idx, 0, QTableWidgetItem(name))
            self.table.setItem(idx, 1, QTableWidgetItem("N/A"))

        layout.addWidget(self.table)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content)
        self.setWidget(scroll)

    def set_result(self, result: AnalysisResult) -> None:
        if result.modulation_result:
            mod = result.modulation_result.predicted_modulation
            conf = result.modulation_result.confidence * 100.0

            top_cand = ""
            if result.modulation_result.class_probabilities:
                sorted_probs = sorted(
                    result.modulation_result.class_probabilities.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                if sorted_probs:
                    top_cand = sorted_probs[0][0]

            if mod == "UNCERTAIN" and top_cand:
                self.lbl_mod_class.setText(f"UNCERTAIN ({top_cand})")
                self.lbl_confidence.setText(f"Confidence: {conf:.1f}% [{result.modulation_result.model_name}]")
            else:
                self.lbl_mod_class.setText(mod)
                self.lbl_confidence.setText(f"Confidence: {conf:.1f}% [{result.modulation_result.model_name}]")

            color = COLOR_SUCCESS if conf >= 75.0 else (COLOR_WARNING if conf >= 50.0 else "#ff3366")
            self.lbl_mod_class.setStyleSheet(f"color: {color}; font-size: 17pt; font-weight: bold;")
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
        bits_val = "0 bits"
        if result.demodulation_result:
            if result.demodulation_result.evm_rms_pct:
                evm_val = result.demodulation_result.evm_rms_pct.display_str()
            if result.demodulation_result.bits:
                n_b = len(result.demodulation_result.bits)
                lead = "".join(str(b) for b in result.demodulation_result.bits[:16])
                bits_val = f"{n_b:,} bits ({lead}...)"

        fec_val = "Possible convolutional"
        if result.decoding_result:
            if result.decoding_result.fec_type and result.decoding_result.fec_type != "None":
                fec_val = result.decoding_result.fec_type
            elif result.decoding_result.message:
                fec_val = result.decoding_result.message

        sync_val = "Converged" if (result.synchronization_result and result.synchronization_result.converged) else "Unlocked / Bypass"

        row_vals = [cf_val, cfo_val, sr_val, obw_val, bw3_val, snr_val, evm_val, bits_val, fec_val, sync_val]
        for idx, val in enumerate(row_vals):
            self.table.setItem(idx, 1, QTableWidgetItem(val))
