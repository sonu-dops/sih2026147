"""Dedicated Demodulated Bits, Hex Dump, and Framing Inspector View."""

from typing import List, Optional
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import COLOR_PRIMARY_ACCENT, COLOR_SUCCESS, COLOR_WARNING
from signalinsight.core.models import AnalysisResult, DemodulationResult


class DemodulationBitsView(QWidget):
    """
    Detailed Bitstream, Hex Dump, and Framing Inspector.
    Provides complete visibility into the demodulated physical layer bitstream:
    - Raw bit sequence with grouping (nibble, byte, word)
    - Full hex dump with ASCII interpretation
    - Bit pattern search (preambles, sync markers, Barker sequences)
    - Channel coding & framing diagnostics
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.demod_result: Optional[DemodulationResult] = None
        self.analysis_result: Optional[AnalysisResult] = None
        self._raw_bits: List[int] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ----------------------------------------------------
        # Top KPI & Diagnostics Strip
        # ----------------------------------------------------
        strip = QFrame()
        strip.setStyleSheet(
            "background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px;"
        )
        s_layout = QHBoxLayout(strip)
        s_layout.setContentsMargins(4, 2, 4, 2)
        s_layout.setSpacing(10)

        self.kpi_bits = QLabel("Bits: 0")
        self.kpi_bits.setStyleSheet(f"font-weight: bold; font-size: 9pt; color: {COLOR_PRIMARY_ACCENT}; padding: 2px 6px; background: #e0f2fe; border-radius: 3px;")

        self.kpi_symbols = QLabel("Symbols: 0")
        self.kpi_symbols.setStyleSheet("font-weight: bold; font-size: 9pt; color: #1e293b; padding: 2px 6px; background: #f1f5f9; border-radius: 3px;")

        self.kpi_fec = QLabel("Coding: Unconfigured")
        self.kpi_fec.setStyleSheet(f"font-weight: bold; font-size: 9pt; color: {COLOR_SUCCESS}; padding: 2px 6px; background: #ecfdf5; border-radius: 3px;")

        self.kpi_evm = QLabel("EVM RMS: -- %")
        self.kpi_evm.setStyleSheet("font-weight: bold; font-size: 9pt; color: #475569; padding: 2px 6px; background: #f8fafc; border-radius: 3px;")

        s_layout.addWidget(self.kpi_bits)
        s_layout.addWidget(self.kpi_symbols)
        s_layout.addWidget(self.kpi_fec)
        s_layout.addWidget(self.kpi_evm)
        s_layout.addStretch()

        layout.addWidget(strip)

        # ----------------------------------------------------
        # Main Splitter: Raw Bitstream (Top) + Hex Dump (Bottom)
        # ----------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top Pane: Raw Bitstream Inspector
        top_box = QFrame()
        tb_layout = QVBoxLayout(top_box)
        tb_layout.setContentsMargins(2, 2, 2, 2)
        tb_layout.setSpacing(4)

        tb_header = QHBoxLayout()
        lbl_tb = QLabel("RAW DEMODULATED BITSTREAM")
        lbl_tb.setStyleSheet("font-size: 8pt; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        tb_header.addWidget(lbl_tb)
        tb_header.addStretch()

        # Search Bar
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Find pattern (1010, AA)...")
        self.edit_search.setMaximumWidth(150)
        self.btn_search = QPushButton("Find")
        self.btn_search.clicked.connect(self._search_pattern)
        tb_header.addWidget(self.edit_search)
        tb_header.addWidget(self.btn_search)

        lbl_group = QLabel("Grouping:")
        lbl_group.setStyleSheet("font-size: 8pt; color: #64748b;")
        self.combo_group = QComboBox()
        self.combo_group.addItems(["8 bits (Bytes)", "4 bits (Nibbles)", "16 bits (Words)", "Raw continuous"])
        self.combo_group.currentIndexChanged.connect(self._render_views)
        tb_header.addWidget(lbl_group)
        tb_header.addWidget(self.combo_group)

        # Export & Copy actions
        self.btn_copy_all = QPushButton("Copy All")
        self.btn_copy_all.clicked.connect(self._copy_all_bits)
        self.btn_save_bin = QPushButton("Export...")
        self.btn_save_bin.clicked.connect(self._export_bits)
        tb_header.addWidget(self.btn_copy_all)
        tb_header.addWidget(self.btn_save_bin)

        tb_layout.addLayout(tb_header)

        self.txt_raw = QTextEdit()
        self.txt_raw.setReadOnly(True)
        self.txt_raw.setFont(QFont("Consolas", 10))
        self.txt_raw.setStyleSheet(
            "background-color: #0f172a; color: #38bdf8; border: 1px solid #334155; border-radius: 4px; padding: 6px;"
        )
        tb_layout.addWidget(self.txt_raw)
        splitter.addWidget(top_box)

        # Bottom Pane: Formatted Hex & ASCII Table
        bot_box = QFrame()
        bb_layout = QVBoxLayout(bot_box)
        bb_layout.setContentsMargins(2, 2, 2, 2)
        bb_layout.setSpacing(4)

        lbl_bb = QLabel("BYTE & HEX DUMP INSPECTOR (Offset | Hex Bytes | ASCII Decoded)")
        lbl_bb.setStyleSheet("font-size: 8pt; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        bb_layout.addWidget(lbl_bb)

        self.table_hex = QTableWidget(0, 3)
        self.table_hex.setHorizontalHeaderLabels(["Offset", "Hex Bytes (16 bytes/row)", "ASCII Preview"])
        self.table_hex.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_hex.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_hex.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_hex.verticalHeader().setVisible(False)
        self.table_hex.setFont(QFont("Consolas", 10))
        self.table_hex.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        bb_layout.addWidget(self.table_hex)
        splitter.addWidget(bot_box)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def set_result(self, result: AnalysisResult) -> None:
        self.analysis_result = result
        if result.demodulation_result and result.demodulation_result.bits:
            self._raw_bits = list(result.demodulation_result.bits)
            self.kpi_symbols.setText(f"Symbols: {result.demodulation_result.symbol_count:,}")
        else:
            self._raw_bits = []
            self.kpi_symbols.setText("Symbols: 0")

        self.kpi_bits.setText(f"Bits: {len(self._raw_bits):,}")

        if result.decoding_result:
            fec_str = result.decoding_result.fec_type or "Possible convolutional"
            self.kpi_fec.setText(f"Coding: {fec_str}")
        else:
            self.kpi_fec.setText("Coding: Possible convolutional")

        if result.demodulation_result and result.demodulation_result.evm_rms_pct:
            val = result.demodulation_result.evm_rms_pct.value
            self.kpi_evm.setText(f"EVM RMS: {val:.2f}%" if val else "EVM RMS: -- %")
        else:
            self.kpi_evm.setText("EVM RMS: -- %")

        self._render_views()

    def _render_views(self) -> None:
        if not self._raw_bits:
            self.txt_raw.setText("No demodulated bitstream available. Load a signal and click RUN ANALYSIS.")
            self.table_hex.setRowCount(0)
            return

        # 1. Render Raw Bit Text
        group_opt = self.combo_group.currentText()
        step = 8
        if "4 bits" in group_opt:
            step = 4
        elif "16 bits" in group_opt:
            step = 16
        elif "Raw" in group_opt:
            step = len(self._raw_bits)

        chunks = []
        limit = min(len(self._raw_bits), 8192)
        for i in range(0, limit, step):
            c = "".join(str(b) for b in self._raw_bits[i : i + step])
            chunks.append(c)

        text = " ".join(chunks)
        if len(self._raw_bits) > limit:
            text += f"\n... [Truncated for display: total {len(self._raw_bits):,} bits] ..."
        self.txt_raw.setText(text)

        # 2. Render Hex & ASCII Table
        bytes_list = []
        for i in range(0, len(self._raw_bits), 8):
            b_chunk = self._raw_bits[i : i + 8]
            val = 0
            for bit in b_chunk:
                val = (val << 1) | bit
            bytes_list.append(val)

        row_count = min((len(bytes_list) + 15) // 16, 512)
        self.table_hex.setRowCount(row_count)

        for r in range(row_count):
            start = r * 16
            row_bytes = bytes_list[start : start + 16]
            offset_str = f"0x{start:04X}"
            hex_str = " ".join(f"{b:02X}" for b in row_bytes)
            ascii_chars = "".join(chr(b) if 32 <= b <= 126 else "." for b in row_bytes)

            self.table_hex.setItem(r, 0, QTableWidgetItem(offset_str))
            self.table_hex.setItem(r, 1, QTableWidgetItem(hex_str))
            self.table_hex.setItem(r, 2, QTableWidgetItem(ascii_chars))

    def _search_pattern(self) -> None:
        pattern = self.edit_search.text().strip()
        if not pattern or not self._raw_bits:
            return

        bit_str = "".join(str(b) for b in self._raw_bits)
        idx = bit_str.find(pattern)
        if idx != -1:
            QMessageBox.information(
                self,
                "Pattern Found",
                f"Pattern '{pattern}' found at bit offset {idx:,} (byte offset {idx//8:,}).",
            )
        else:
            QMessageBox.warning(self, "Pattern Not Found", f"Pattern '{pattern}' was not found in the demodulated bitstream.")

    def _copy_all_bits(self) -> None:
        if not self._raw_bits:
            return
        bit_str = "".join(str(b) for b in self._raw_bits)
        QApplication.clipboard().setText(bit_str)
        self.btn_copy_all.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.btn_copy_all.setText("Copy All Bits"))

    def _export_bits(self) -> None:
        if not self._raw_bits:
            QMessageBox.information(self, "No Bits", "No demodulated bits to export.")
            return

        fn, _ = QFileDialog.getSaveFileName(
            self, "Export Demodulated Bitstream", "demodulated_bits.txt", "Text Files (*.txt);;Binary Files (*.bin)"
        )
        if not fn:
            return

        try:
            if fn.endswith(".bin"):
                byte_arr = bytearray()
                for i in range(0, len(self._raw_bits), 8):
                    val = 0
                    for bit in self._raw_bits[i : i + 8]:
                        val = (val << 1) | bit
                    byte_arr.append(val)
                with open(fn, "wb") as f:
                    f.write(byte_arr)
            else:
                bit_str = "".join(str(b) for b in self._raw_bits)
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(bit_str)
            QMessageBox.information(self, "Export Complete", f"Successfully saved {len(self._raw_bits):,} bits to:\n{fn}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not write file: {e}")
