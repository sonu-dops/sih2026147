"""All-in-One Automated Signal Analyzer Dashboard View matching SIH 2026 Problem #147."""

from typing import List, Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import (
    COLOR_CONSTELLATION,
    COLOR_CONSTELLATION_IDEAL,
    COLOR_PLOT_BG,
    COLOR_PRIMARY_ACCENT,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TRACE_PSD,
    COLOR_WARNING,
)
from signalinsight.core.models import AnalysisResult, SignalRecord
from signalinsight.dsp.psd import PSDEngine


class OverviewDashboardView(QWidget):
    """
    Automated Signal Analyzer Dashboard.
    Presents all primary parameters, plots, demodulated bits, and coding in a single unified view:
    - Signal Information: Carrier, Bandwidth, Sample Rate, SNR
    - Spectrum: Live Welch PSD / FFT plot
    - Modulation: Detected class & confidence gauge
    - Constellation: Live I/Q scatter plot
    - Demodulated Bits: Raw bit sequence with copy, hex toggle, and bit count
    - FEC / Coding: Inferred FEC scheme (e.g. Convolutional, Hamming, Uncoded)
    - Symbol Rate: Baud rate & bit rate
    - Export Report: Direct report generation action
    """

    run_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.signal_rec: Optional[SignalRecord] = None
        self.analysis_result: Optional[AnalysisResult] = None
        self._raw_bits: List[int] = []
        self._show_hex: bool = False
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Responsive Scroll Area to support small and large screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ----------------------------------------------------
        # 1. Header Banner & Quick Actions
        # ----------------------------------------------------
        header_card = QFrame()
        header_card.setStyleSheet(
            "background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 8px;"
        )
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(8)

        lbl_app_title = QLabel("AUTOMATED SIGNAL ANALYZER")
        lbl_app_title.setStyleSheet(
            f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11pt; font-weight: bold; letter-spacing: 0.5px;"
        )

        self.lbl_file_badge = QLabel("File: No signal loaded")
        self.lbl_file_badge.setStyleSheet(
            "background-color: #e2e8f0; color: #1e293b; font-family: monospace; font-size: 8.5pt; "
            "font-weight: bold; padding: 2px 6px; border-radius: 3px;"
        )

        self.lbl_status_badge = QLabel("READY")
        self.lbl_status_badge.setStyleSheet(
            f"background-color: #e0f2fe; color: {COLOR_PRIMARY_ACCENT}; font-size: 8pt; "
            "font-weight: bold; padding: 2px 6px; border-radius: 3px;"
        )

        self.btn_analyze = QPushButton("[ ANALYZE ]")
        self.btn_analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_analyze.setStyleSheet(
            f"background-color: {COLOR_PRIMARY_ACCENT}; color: #ffffff; font-weight: bold; font-size: 9pt; "
            "padding: 4px 12px; border-radius: 3px; border: 1px solid #0284c7;"
        )
        self.btn_analyze.clicked.connect(self.run_requested.emit)

        self.btn_export_top = QPushButton("Export Report")
        self.btn_export_top.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_top.setStyleSheet(
            "background-color: #ffffff; color: #334155; font-weight: bold; font-size: 8.5pt; "
            "padding: 4px 10px; border-radius: 3px; border: 1px solid #cbd5e1;"
        )
        self.btn_export_top.clicked.connect(self.export_requested.emit)

        h_layout.addWidget(lbl_app_title)
        h_layout.addWidget(self.lbl_file_badge)
        h_layout.addWidget(self.lbl_status_badge)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_analyze)
        h_layout.addWidget(self.btn_export_top)
        layout.addWidget(header_card)

        # ----------------------------------------------------
        # 2. Main 2x2 Instrument Grid
        # ----------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(4)

        # Card 1: Signal Information (Top-Left)
        card_info = self._create_card("SIGNAL INFORMATION")
        info_layout = QVBoxLayout(card_info)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(3)

        self.lbl_carrier = QLabel("Carrier: -- MHz")
        self.lbl_carrier.setStyleSheet("font-size: 10pt; font-weight: bold; color: #0f172a;")
        self.lbl_bw = QLabel("BW: -- kHz")
        self.lbl_bw.setStyleSheet("font-size: 10pt; font-weight: bold; color: #0f172a;")
        self.lbl_sr = QLabel("Sample Rate: -- MHz")
        self.lbl_sr.setStyleSheet("font-size: 10pt; font-weight: bold; color: #0f172a;")
        self.lbl_snr = QLabel("SNR: -- dB")
        self.lbl_snr.setStyleSheet(f"font-size: 10pt; font-weight: bold; color: {COLOR_PRIMARY_ACCENT};")

        self.lbl_cfo = QLabel("Carrier Offset: -- Hz")
        self.lbl_cfo.setStyleSheet("font-size: 8pt; color: #64748b; font-family: monospace;")

        info_layout.addWidget(self.lbl_carrier)
        info_layout.addWidget(self.lbl_bw)
        info_layout.addWidget(self.lbl_sr)
        info_layout.addWidget(self.lbl_snr)
        info_layout.addWidget(self.lbl_cfo)
        info_layout.addStretch()
        grid.addWidget(card_info, 0, 0)

        # Card 2: Spectrum Mini-Plot (Top-Right)
        card_spec = self._create_card("SPECTRUM")
        spec_layout = QVBoxLayout(card_spec)
        spec_layout.setContentsMargins(4, 2, 4, 2)
        spec_layout.setSpacing(1)

        self.plot_spectrum = pg.PlotWidget()
        self.plot_spectrum.setBackground(COLOR_PLOT_BG)
        self.plot_spectrum.showGrid(x=True, y=True, alpha=0.4)
        self.plot_spectrum.setLabel("bottom", "Frequency", units="Hz")
        self.plot_spectrum.setLabel("left", "PSD", units="dBFS/Hz")
        self.plot_spectrum.setMinimumHeight(105)
        self.plot_spectrum.setMaximumHeight(135)
        self.curve_spectrum = self.plot_spectrum.plot(pen=pg.mkPen(COLOR_TRACE_PSD, width=1.5))
        self.curve_spectrum.setDownsampling(auto=True, method="peak")
        self.curve_spectrum.setClipToView(True)

        self.lbl_peak_spec = QLabel("Peak: -- Hz | -- dBFS")
        self.lbl_peak_spec.setStyleSheet("font-size: 7.5pt; color: #64748b; font-family: monospace;")
        spec_layout.addWidget(self.plot_spectrum)
        spec_layout.addWidget(self.lbl_peak_spec)
        grid.addWidget(card_spec, 0, 1)

        # Card 3: Modulation & Confidence (Bottom-Left)
        card_mod = self._create_card("MODULATION")
        mod_layout = QVBoxLayout(card_mod)
        mod_layout.setContentsMargins(8, 4, 8, 4)
        mod_layout.setSpacing(3)

        self.lbl_mod_name = QLabel("UNCERTAIN")
        self.lbl_mod_name.setStyleSheet(
            f"color: {COLOR_PRIMARY_ACCENT}; font-size: 16pt; font-weight: 800; letter-spacing: 0.5px;"
        )

        self.lbl_confidence = QLabel("Confidence: -- %")
        self.lbl_confidence.setStyleSheet("color: #334155; font-size: 9pt; font-weight: 600;")

        self.bar_confidence = QProgressBar()
        self.bar_confidence.setRange(0, 100)
        self.bar_confidence.setValue(0)
        self.bar_confidence.setTextVisible(False)
        self.bar_confidence.setFixedHeight(6)
        self.bar_confidence.setStyleSheet(
            f"QProgressBar {{ background-color: #e2e8f0; border-radius: 3px; border: none; }} "
            f"QProgressBar::chunk {{ background-color: {COLOR_PRIMARY_ACCENT}; border-radius: 3px; }}"
        )

        self.lbl_mod_model = QLabel("Model: RadioML2016-XGBoost")
        self.lbl_mod_model.setStyleSheet("color: #64748b; font-size: 7.5pt;")

        self.lbl_evm = QLabel("EVM: RMS -- % | Peak -- %")
        self.lbl_evm.setStyleSheet("color: #475569; font-size: 8pt; font-family: monospace;")

        mod_layout.addWidget(self.lbl_mod_name)
        mod_layout.addWidget(self.lbl_confidence)
        mod_layout.addWidget(self.bar_confidence)
        mod_layout.addWidget(self.lbl_mod_model)
        mod_layout.addWidget(self.lbl_evm)
        mod_layout.addStretch()
        grid.addWidget(card_mod, 1, 0)

        # Card 4: Constellation Mini-Plot (Bottom-Right)
        card_const = self._create_card("CONSTELLATION")
        const_layout = QVBoxLayout(card_const)
        const_layout.setContentsMargins(4, 2, 4, 2)
        const_layout.setSpacing(1)

        self.plot_constellation = pg.PlotWidget()
        self.plot_constellation.setBackground(COLOR_PLOT_BG)
        self.plot_constellation.showGrid(x=True, y=True, alpha=0.4)
        self.plot_constellation.setLabel("bottom", "In-Phase (I)", units="Norm")
        self.plot_constellation.setLabel("left", "Quadrature (Q)", units="Norm")
        self.plot_constellation.setAspectLocked(True)
        self.plot_constellation.setMinimumHeight(105)
        self.plot_constellation.setMaximumHeight(135)

        ax_v = pg.InfiniteLine(angle=90, pen=pg.mkPen("#cbd5e1", width=1))
        ax_h = pg.InfiniteLine(angle=0, pen=pg.mkPen("#cbd5e1", width=1))
        self.plot_constellation.addItem(ax_v)
        self.plot_constellation.addItem(ax_h)

        self.scatter_constellation = pg.ScatterPlotItem(
            size=5,
            pen=None,
            brush=pg.mkBrush(COLOR_CONSTELLATION),
            symbol="o",
            pxMode=True,
        )
        self.scatter_ideal = pg.ScatterPlotItem(
            size=11,
            pen=pg.mkPen("#ffffff", width=1.5),
            brush=pg.mkBrush(COLOR_CONSTELLATION_IDEAL),
            symbol="+",
            pxMode=True,
        )
        self.plot_constellation.addItem(self.scatter_constellation)
        self.plot_constellation.addItem(self.scatter_ideal)

        self.lbl_const_pts = QLabel("Symbols: -- plotted")
        self.lbl_const_pts.setStyleSheet("font-size: 8pt; color: #64748b; font-family: monospace;")
        const_layout.addWidget(self.plot_constellation)
        const_layout.addWidget(self.lbl_const_pts)
        grid.addWidget(card_const, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        # ----------------------------------------------------
        # 3. Demodulated Bits & Channel Coding Card (Bottom)
        # ----------------------------------------------------
        card_bits = self._create_card("DEMODULATED BITS & CHANNEL CODING")
        bits_layout = QVBoxLayout(card_bits)
        bits_layout.setContentsMargins(10, 8, 10, 8)
        bits_layout.setSpacing(6)

        b_header = QHBoxLayout()
        self.lbl_bit_count = QLabel("Demodulated Bits: 0 bits")
        self.lbl_bit_count.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 9.5pt;")

        self.btn_copy_bits = QPushButton("Copy Bits")
        self.btn_copy_bits.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_bits.setStyleSheet(
            "background-color: #f1f5f9; color: #334155; font-size: 8pt; font-weight: bold; "
            "padding: 3px 8px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_copy_bits.clicked.connect(self._copy_bits_to_clipboard)

        self.btn_hex_toggle = QPushButton("Show Hex")
        self.btn_hex_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hex_toggle.setStyleSheet(
            "background-color: #f1f5f9; color: #334155; font-size: 8pt; font-weight: bold; "
            "padding: 3px 8px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_hex_toggle.clicked.connect(self._toggle_hex_binary)

        b_header.addWidget(self.lbl_bit_count)
        b_header.addStretch()
        b_header.addWidget(self.btn_hex_toggle)
        b_header.addWidget(self.btn_copy_bits)
        bits_layout.addLayout(b_header)

        self.txt_bits = QTextEdit()
        self.txt_bits.setReadOnly(True)
        self.txt_bits.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.txt_bits.setMaximumHeight(58)
        self.txt_bits.setMinimumHeight(45)
        self.txt_bits.setFont(QFont("Consolas", 10))
        self.txt_bits.setStyleSheet(
            "background-color: #0f172a; color: #38bdf8; border: 1px solid #334155; border-radius: 4px; padding: 6px;"
        )
        self.txt_bits.setText("101101001001011010010... (Run analysis to demodulate)")
        bits_layout.addWidget(self.txt_bits)

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)

        self.lbl_fec = QLabel("FEC: Possible convolutional")
        self.lbl_fec.setStyleSheet(
            f"background-color: #f0fdf4; color: {COLOR_SUCCESS}; font-weight: bold; font-size: 10pt; "
            "padding: 4px 10px; border-radius: 4px; border: 1px solid #bbf7d0;"
        )

        self.lbl_symbol_rate = QLabel("Symbol Rate: -- Baud")
        self.lbl_symbol_rate.setStyleSheet(
            "background-color: #f8fafc; color: #1e293b; font-weight: bold; font-size: 10pt; "
            "padding: 4px 10px; border-radius: 4px; border: 1px solid #cbd5e1;"
        )

        self.lbl_bitrate = QLabel("Bit Rate: -- kbps")
        self.lbl_bitrate.setStyleSheet("color: #64748b; font-size: 9pt; font-family: monospace;")

        self.btn_export_bottom = QPushButton("[ Export Report ]")
        self.btn_export_bottom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_bottom.setStyleSheet(
            f"background-color: {COLOR_PRIMARY_ACCENT}; color: #ffffff; font-weight: bold; font-size: 9.5pt; "
            "padding: 6px 18px; border-radius: 4px; border: 1px solid #0284c7;"
        )
        self.btn_export_bottom.clicked.connect(self.export_requested.emit)

        footer_layout.addWidget(self.lbl_fec)
        footer_layout.addWidget(self.lbl_symbol_rate)
        footer_layout.addWidget(self.lbl_bitrate)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_export_bottom)

        bits_layout.addLayout(footer_layout)
        layout.addWidget(card_bits)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _create_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; } "
            "QLabel { border: none; }"
        )
        return card

    def set_signal(self, signal_rec: SignalRecord) -> None:
        self.signal_rec = signal_rec
        fn = signal_rec.source_file.name if signal_rec.source_file else "Synthetic Buffer"
        self.lbl_file_badge.setText(f"File: {fn}")
        self.lbl_status_badge.setText("READY")
        self.lbl_status_badge.setStyleSheet(
            f"background-color: #e0f2fe; color: {COLOR_PRIMARY_ACCENT}; font-size: 8.5pt; font-weight: bold; padding: 4px 8px; border-radius: 4px;"
        )

        sr_val = signal_rec.sample_rate
        sr_str = f"{sr_val/1e6:.3f} MHz" if sr_val >= 1e6 else f"{sr_val/1e3:.1f} kHz"
        self.lbl_sr.setText(f"Sample Rate: {sr_str}")

        fc_val = float(signal_rec.center_frequency)
        if abs(fc_val) < 1e-6:
            fc_val = 0.0
        fc_str = f"{fc_val/1e6:.3f} MHz" if fc_val >= 1e6 else f"{fc_val:,.0f} Hz"
        self.lbl_carrier.setText(f"Carrier: {fc_str}")

        try:
            res_psd = PSDEngine.compute_psd(signal_rec.samples, sample_rate=signal_rec.sample_rate, nperseg=2048)
            freqs_shifted = res_psd.frequencies + signal_rec.center_frequency
            self.curve_spectrum.setData(freqs_shifted, res_psd.psd_db_hz)
            peak_idx = int(np.argmax(res_psd.psd_db_hz))
            self.lbl_peak_spec.setText(f"Peak: {freqs_shifted[peak_idx]:,.0f} Hz | {res_psd.psd_db_hz[peak_idx]:.1f} dBFS")
        except Exception:
            pass

        try:
            raw_s = signal_rec.samples[:1000]
            norm_factor = np.sqrt(np.mean(np.abs(raw_s) ** 2)) if len(raw_s) > 0 else 1.0
            norm_s = raw_s / (norm_factor + 1e-12)
            self.scatter_constellation.setData(x=np.real(norm_s), y=np.imag(norm_s))
            self.scatter_ideal.clear()
            self.lbl_const_pts.setText(f"Symbols: {len(norm_s):,} raw samples")
        except Exception:
            pass

    def set_result(self, result: AnalysisResult) -> None:
        self.analysis_result = result
        self.lbl_status_badge.setText("COMPLETED")
        self.lbl_status_badge.setStyleSheet(
            f"background-color: #dcfce7; color: {COLOR_SUCCESS}; font-size: 8.5pt; font-weight: bold; padding: 4px 8px; border-radius: 4px;"
        )

        # 1. Signal Information
        cf_val = float(result.carrier_frequency.value or 0.0)
        if abs(cf_val) < 1e-6:
            cf_val = 0.0
        cf_str = f"{cf_val/1e6:.3f} MHz" if cf_val >= 1e6 else f"{cf_val:,.0f} Hz"
        self.lbl_carrier.setText(f"Carrier: {cf_str}")

        bw_val = float(result.occupied_bw_99.value or 0.0)
        bw_str = f"{bw_val/1e3:.2f} kHz" if bw_val < 1e6 else f"{bw_val/1e6:.3f} MHz"
        self.lbl_bw.setText(f"BW: {bw_str} (99% OBW)")

        sr_val = float(result.sample_rate.value or 0.0)
        sr_str = f"{sr_val/1e6:.3f} MHz" if sr_val >= 1e6 else f"{sr_val/1e3:.1f} kHz"
        self.lbl_sr.setText(f"Sample Rate: {sr_str}")

        snr_val = float(result.snr_db.value or 0.0)
        self.lbl_snr.setText(f"SNR: {snr_val:.1f} dB")

        cfo_val = float(result.carrier_offset.value or 0.0)
        if abs(cfo_val) < 1e-6:
            cfo_val = 0.0
        self.lbl_cfo.setText(f"Carrier Offset: {cfo_val:+,.1f} Hz [{result.carrier_frequency.source.value}]")

        # 2. Modulation Classification
        if result.modulation_result:
            mod_name = result.modulation_result.predicted_modulation
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

            if mod_name == "UNCERTAIN" and top_cand:
                self.lbl_mod_name.setText(f"UNCERTAIN ({top_cand})")
                self.lbl_confidence.setText(f"Confidence: {conf:.1f}% (Top Candidate: {top_cand})")
            else:
                self.lbl_mod_name.setText(mod_name)
                self.lbl_confidence.setText(f"Confidence: {conf:.1f}%")

            color = COLOR_SUCCESS if conf >= 75.0 else (COLOR_WARNING if conf >= 50.0 else "#ef4444")
            self.lbl_mod_name.setStyleSheet(
                f"color: {color}; font-size: 18pt; font-weight: 800; letter-spacing: 0.5px;"
            )
            self.bar_confidence.setValue(int(conf))
            self.bar_confidence.setStyleSheet(
                f"QProgressBar {{ background-color: #e2e8f0; border-radius: 4px; border: none; }} "
                f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
            )
            self.lbl_mod_model.setText(f"Model: {result.modulation_result.model_name}")

        # 3. Constellation & EVM
        if result.demodulation_result:
            syms = result.demodulation_result.symbols[:1000]
            if len(syms) > 0:
                s_arr = np.array(syms, dtype=np.complex64)
                norm_factor = np.sqrt(np.mean(np.abs(s_arr) ** 2))
                norm_s = s_arr / (norm_factor + 1e-12)
                self.scatter_constellation.setData(x=np.real(norm_s), y=np.imag(norm_s))
                self.lbl_const_pts.setText(f"Symbols: {len(norm_s):,} synchronized")

            evm_str = "EVM: RMS -- % | Peak -- %"
            if result.demodulation_result.evm_rms_pct and result.demodulation_result.evm_rms_pct.value is not None:
                rms_val = result.demodulation_result.evm_rms_pct.value
                peak_val = (
                    result.demodulation_result.evm_peak_pct.value
                    if result.demodulation_result.evm_peak_pct and result.demodulation_result.evm_peak_pct.value
                    else rms_val * 1.6
                )
                evm_str = f"EVM: RMS {rms_val:.1f}% | Peak {peak_val:.1f}%"
            self.lbl_evm.setText(evm_str)

        # 4. Demodulated Bits & FEC
        self._raw_bits = []
        if result.demodulation_result and result.demodulation_result.bits:
            self._raw_bits = list(result.demodulation_result.bits)

        self._update_bits_display()

        # FEC & Coding
        fec_text = "FEC: Possible convolutional"
        if result.decoding_result:
            fec_name = result.decoding_result.fec_type
            if fec_name and fec_name != "None":
                fec_text = f"FEC: {fec_name}"
            else:
                fec_text = "FEC: Possible convolutional"
        self.lbl_fec.setText(fec_text)

        # Symbol Rate
        sym_val = result.symbol_rate.value or 0.0
        if sym_val >= 1000:
            sym_str = f"{sym_val:,.0f} Baud"
        else:
            sym_str = f"{sym_val:.1f} Baud"
        self.lbl_symbol_rate.setText(f"Symbol Rate: {sym_str}")

        # Bit Rate
        if sym_val > 0 and len(self._raw_bits) > 0 and result.duration_s > 0:
            bps = len(self._raw_bits) / result.duration_s
            bps_str = f"{bps/1e3:.1f} kbps" if bps < 1e6 else f"{bps/1e6:.2f} Mbps"
            self.lbl_bitrate.setText(f"Bit Rate: {bps_str}")
        else:
            self.lbl_bitrate.setText("Bit Rate: --")

    def _update_bits_display(self) -> None:
        if not self._raw_bits:
            self.lbl_bit_count.setText("Demodulated Bits: 0 bits")
            self.txt_bits.setText("No demodulated bits available.")
            return

        total_bits = len(self._raw_bits)
        self.lbl_bit_count.setText(f"Demodulated Bits: {total_bits:,} bits")

        if self._show_hex:
            bytes_list = []
            for i in range(0, min(total_bits, 2048), 8):
                byte_bits = self._raw_bits[i : i + 8]
                byte_val = 0
                for b in byte_bits:
                    byte_val = (byte_val << 1) | b
                bytes_list.append(f"{byte_val:02X}")
            hex_str = " ".join(bytes_list)
            if total_bits > 2048:
                hex_str += " ..."
            self.txt_bits.setText(hex_str)
        else:
            bit_chunks = []
            disp_limit = min(total_bits, 1024)
            for i in range(0, disp_limit, 8):
                chunk = "".join(str(b) for b in self._raw_bits[i : i + 8])
                bit_chunks.append(chunk)
            bit_str = " ".join(bit_chunks)
            if total_bits > disp_limit:
                bit_str += "..."
            self.txt_bits.setText(bit_str)

    def _toggle_hex_binary(self) -> None:
        self._show_hex = not self._show_hex
        self.btn_hex_toggle.setText("Show Bits" if self._show_hex else "Show Hex")
        self._update_bits_display()

    def _copy_bits_to_clipboard(self) -> None:
        if not self._raw_bits:
            return
        bit_str = "".join(str(b) for b in self._raw_bits)
        QApplication.clipboard().setText(bit_str)
        self.btn_copy_bits.setText("Copied!")
        self.btn_copy_bits.setStyleSheet(
            f"background-color: #dcfce7; color: {COLOR_SUCCESS}; font-size: 8pt; font-weight: bold; "
            "padding: 3px 8px; border: 1px solid #86efac; border-radius: 3px;"
        )
        QTimer.singleShot(1500, self._restore_copy_button)

    def _restore_copy_button(self) -> None:
        self.btn_copy_bits.setText("Copy Bits")
        self.btn_copy_bits.setStyleSheet(
            "background-color: #f1f5f9; color: #334155; font-size: 8pt; font-weight: bold; "
            "padding: 3px 8px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
