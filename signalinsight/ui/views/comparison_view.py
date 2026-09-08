"""Signal comparison mode: side-by-side inspection of two RF recordings."""

from pathlib import Path
from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import (
    COLOR_PLOT_BG,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    COLOR_WARNING,
)
from signalinsight.core.models import AnalysisResult, SignalRecord
from signalinsight.dsp.fft import FFTEngine


class ComparisonView(QWidget):
    """Side-by-side time domain and spectral comparison of two signals."""

    request_current_signal = pyqtSignal(str)  # Emits "A" or "B"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.sig_a: Optional[SignalRecord] = None
        self.res_a: Optional[AnalysisResult] = None
        self.sig_b: Optional[SignalRecord] = None
        self.res_b: Optional[AnalysisResult] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        pg.setConfigOptions(antialias=False, enableExperimental=True)

        # ----------------------------------------------------
        # Top Instruction & Control Bar
        # ----------------------------------------------------
        top_bar = QFrame()
        top_bar.setStyleSheet(
            "background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 8px;"
        )
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(4, 2, 4, 2)
        tb_layout.setSpacing(8)

        self.lbl_guide = QLabel(
            "Dual Comparison Mode: Compare two signals side-by-side. Load Signal A and Signal B below."
        )
        self.lbl_guide.setStyleSheet("color: #475569; font-size: 8.5pt; font-weight: 600;")
        tb_layout.addWidget(self.lbl_guide)
        tb_layout.addStretch()

        self.btn_use_current_b = QPushButton("Compare with Current File (as B)")
        self.btn_use_current_b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_use_current_b.setStyleSheet(
            f"background-color: #f1f5f9; color: {COLOR_WARNING}; font-weight: bold; font-size: 8pt; "
            "padding: 3px 8px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_use_current_b.clicked.connect(lambda: self.request_current_signal.emit("B"))
        tb_layout.addWidget(self.btn_use_current_b)

        layout.addWidget(top_bar)

        # ----------------------------------------------------
        # Main Splitter (Left: Signal A, Right: Signal B)
        # ----------------------------------------------------
        splitter = QSplitter()

        # Left Panel (Signal A)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(3)

        header_a = QHBoxLayout()
        self.lbl_sig_a = QLabel("Signal A: (None loaded)")
        self.lbl_sig_a.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-weight: bold; font-size: 9.5pt;")
        self.btn_load_a = QPushButton("Load File A...")
        self.btn_load_a.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_a.setStyleSheet(
            f"background-color: #f1f5f9; color: {COLOR_PRIMARY_ACCENT}; font-size: 8pt; font-weight: bold; "
            "padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_load_a.clicked.connect(self._on_load_a_clicked)

        self.btn_use_curr_a = QPushButton("Use Current")
        self.btn_use_curr_a.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_use_curr_a.setStyleSheet(
            "background-color: #f1f5f9; color: #334155; font-size: 8pt; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_use_curr_a.clicked.connect(lambda: self.request_current_signal.emit("A"))

        header_a.addWidget(self.lbl_sig_a)
        header_a.addStretch()
        header_a.addWidget(self.btn_use_curr_a)
        header_a.addWidget(self.btn_load_a)
        left_layout.addLayout(header_a)

        self.plot_a_time = pg.PlotWidget()
        self.plot_a_time.setBackground(COLOR_PLOT_BG)
        self.plot_a_time.showGrid(x=True, y=True, alpha=0.5)
        self.plot_a_time.setLabel("bottom", "Time", units="s")
        self.plot_a_time.setLabel("left", "Amplitude (I)")

        self.plot_a_spec = pg.PlotWidget()
        self.plot_a_spec.setBackground(COLOR_PLOT_BG)
        self.plot_a_spec.showGrid(x=True, y=True, alpha=0.5)
        self.plot_a_spec.setLabel("bottom", "Frequency", units="Hz")
        self.plot_a_spec.setLabel("left", "Power", units="dBFS")

        left_layout.addWidget(self.plot_a_time)
        left_layout.addWidget(self.plot_a_spec)
        splitter.addWidget(left_widget)

        # Right Panel (Signal B)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(3)

        header_b = QHBoxLayout()
        self.lbl_sig_b = QLabel("Signal B: (None loaded)")
        self.lbl_sig_b.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold; font-size: 9.5pt;")
        self.btn_load_b = QPushButton("Load File B...")
        self.btn_load_b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_b.setStyleSheet(
            f"background-color: #f1f5f9; color: {COLOR_WARNING}; font-size: 8pt; font-weight: bold; "
            "padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_load_b.clicked.connect(self._on_load_b_clicked)

        self.btn_use_curr_b = QPushButton("Use Current")
        self.btn_use_curr_b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_use_curr_b.setStyleSheet(
            "background-color: #f1f5f9; color: #334155; font-size: 8pt; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 3px;"
        )
        self.btn_use_curr_b.clicked.connect(lambda: self.request_current_signal.emit("B"))

        header_b.addWidget(self.lbl_sig_b)
        header_b.addStretch()
        header_b.addWidget(self.btn_use_curr_b)
        header_b.addWidget(self.btn_load_b)
        right_layout.addLayout(header_b)

        self.plot_b_time = pg.PlotWidget()
        self.plot_b_time.setBackground(COLOR_PLOT_BG)
        self.plot_b_time.showGrid(x=True, y=True, alpha=0.5)
        self.plot_b_time.setLabel("bottom", "Time", units="s")
        self.plot_b_time.setLabel("left", "Amplitude (I)")

        self.plot_b_spec = pg.PlotWidget()
        self.plot_b_spec.setBackground(COLOR_PLOT_BG)
        self.plot_b_spec.showGrid(x=True, y=True, alpha=0.5)
        self.plot_b_spec.setLabel("bottom", "Frequency", units="Hz")
        self.plot_b_spec.setLabel("left", "Power", units="dBFS")

        right_layout.addWidget(self.plot_b_time)
        right_layout.addWidget(self.plot_b_spec)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter, stretch=2)

        # ----------------------------------------------------
        # Bottom Comparison Metrics Table
        # ----------------------------------------------------
        self.metrics_table = QTableWidget(7, 3)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Signal A", "Signal B"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metrics_table.setMinimumHeight(140)
        self.metrics_table.setMaximumHeight(200)

        metrics = [
            "Modulation Class",
            "Classification Confidence",
            "Carrier Frequency",
            "Symbol Rate",
            "99% Occupied Bandwidth",
            "Signal-to-Noise Ratio (SNR)",
            "RMS EVM",
        ]
        for row, m in enumerate(metrics):
            self.metrics_table.setItem(row, 0, QTableWidgetItem(m))
            self.metrics_table.setItem(row, 1, QTableWidgetItem("N/A"))
            self.metrics_table.setItem(row, 2, QTableWidgetItem("N/A"))

        layout.addWidget(self.metrics_table, stretch=1)

    def set_signal_a(self, sig: SignalRecord, res: Optional[AnalysisResult] = None) -> None:
        self.sig_a = sig
        self.res_a = res

        fn = sig.source_file.name if sig.source_file else "Active Signal A"
        self.lbl_sig_a.setText(f"Signal A: {fn}")

        t_a = np.arange(min(len(sig.samples), 5000)) / sig.sample_rate
        s_a = sig.samples[: len(t_a)]
        self.plot_a_time.clear()
        c_at = self.plot_a_time.plot(t_a, s_a.real, pen=COLOR_PRIMARY_ACCENT)
        c_at.setDownsampling(auto=True, method="peak")
        c_at.setClipToView(True)

        spec_a = FFTEngine.compute_spectrum(sig.samples, sample_rate=sig.sample_rate, fft_size=2048)
        self.plot_a_spec.clear()
        c_as = self.plot_a_spec.plot(spec_a.frequencies, spec_a.power_db, pen=COLOR_PRIMARY_ACCENT)
        c_as.setDownsampling(auto=True, method="peak")
        c_as.setClipToView(True)

        if res:
            self._fill_col(1, res)
        else:
            self._analyze_and_fill_col(1, sig)

        self._update_guide()

    def set_signal_b(self, sig: SignalRecord, res: Optional[AnalysisResult] = None) -> None:
        self.sig_b = sig
        self.res_b = res

        fn = sig.source_file.name if sig.source_file else "Active Signal B"
        self.lbl_sig_b.setText(f"Signal B: {fn}")

        t_b = np.arange(min(len(sig.samples), 5000)) / sig.sample_rate
        s_b = sig.samples[: len(t_b)]
        self.plot_b_time.clear()
        c_bt = self.plot_b_time.plot(t_b, s_b.real, pen=COLOR_WARNING)
        c_bt.setDownsampling(auto=True, method="peak")
        c_bt.setClipToView(True)

        spec_b = FFTEngine.compute_spectrum(sig.samples, sample_rate=sig.sample_rate, fft_size=2048)
        self.plot_b_spec.clear()
        c_bs = self.plot_b_spec.plot(spec_b.frequencies, spec_b.power_db, pen=COLOR_WARNING)
        c_bs.setDownsampling(auto=True, method="peak")
        c_bs.setClipToView(True)

        if res:
            self._fill_col(2, res)
        else:
            self._analyze_and_fill_col(2, sig)

        self._update_guide()

    def set_signals(
        self,
        sig_a: SignalRecord,
        res_a: Optional[AnalysisResult],
        sig_b: SignalRecord,
        res_b: Optional[AnalysisResult],
    ) -> None:
        self.set_signal_a(sig_a, res_a)
        self.set_signal_b(sig_b, res_b)

    def _update_guide(self) -> None:
        if self.sig_a and self.sig_b:
            fn_a = self.sig_a.source_file.name if self.sig_a.source_file else "Signal A"
            fn_b = self.sig_b.source_file.name if self.sig_b.source_file else "Signal B"
            self.lbl_guide.setText(f"Comparing: {fn_a} (Left / Cyan) vs {fn_b} (Right / Orange)")
            self.lbl_guide.setStyleSheet("color: #16a34a; font-size: 8.5pt; font-weight: bold;")
        elif self.sig_a:
            fn_a = self.sig_a.source_file.name if self.sig_a.source_file else "Signal A"
            self.lbl_guide.setText(
                f"Signal A loaded ({fn_a}). Click 'Load File B...' or 'Compare with Current File' to select Signal B."
            )
            self.lbl_guide.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 8.5pt; font-weight: bold;")
        elif self.sig_b:
            fn_b = self.sig_b.source_file.name if self.sig_b.source_file else "Signal B"
            self.lbl_guide.setText(f"Signal B loaded ({fn_b}). Click 'Load File A...' to select Signal A.")
            self.lbl_guide.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 8.5pt; font-weight: bold;")
        else:
            self.lbl_guide.setText(
                "Dual Comparison Mode: Compare two signals side-by-side. Load Signal A and Signal B below."
            )
            self.lbl_guide.setStyleSheet("color: #475569; font-size: 8.5pt; font-weight: 600;")

    def _analyze_and_fill_col(self, col: int, sig: SignalRecord) -> None:
        try:
            from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner
            runner = PipelineRunner()
            opts = PipelineOptions(run_sync=True, run_demod=True, run_decode=False)
            res = runner.run(sig, opts)
            if col == 1:
                self.res_a = res
            else:
                self.res_b = res
            self._fill_col(col, res)
        except Exception:
            pass

    def _fill_col(self, col: int, res: AnalysisResult) -> None:
        mod_str = res.modulation_result.predicted_modulation if res.modulation_result else "N/A"
        conf_str = f"{res.modulation_result.confidence*100:.1f}%" if res.modulation_result else "N/A"
        cf_val = res.carrier_frequency.value or 0.0
        cf_val = 0.0 if abs(cf_val) < 1e-6 else cf_val
        cf_str = f"{cf_val:,.1f} Hz" if cf_val != 0.0 else "0 Hz (Baseband)"
        sr_str = f"{res.symbol_rate.value:,.1f} Baud" if res.symbol_rate.value is not None else "N/A"
        obw_str = f"{res.occupied_bw_99.value:,.1f} Hz" if res.occupied_bw_99.value is not None else "N/A"
        snr_str = f"{res.snr_db.value:.2f} dB" if res.snr_db.value is not None else "N/A"
        evm_str = (
            f"{res.demodulation_result.evm_rms_pct.value:.2f}%"
            if res.demodulation_result and res.demodulation_result.evm_rms_pct
            else "N/A"
        )

        vals = [mod_str, conf_str, cf_str, sr_str, obw_str, snr_str, evm_str]
        for row, v in enumerate(vals):
            self.metrics_table.setItem(row, col, QTableWidgetItem(v))

    def _on_load_a_clicked(self) -> None:
        path = self._pick_file("Select Signal A")
        if path:
            rec = self._load_file(path)
            if rec:
                self.set_signal_a(rec)

    def _on_load_b_clicked(self) -> None:
        path = self._pick_file("Select Signal B")
        if path:
            rec = self._load_file(path)
            if rec:
                self.set_signal_b(rec)

    def _pick_file(self, title: str) -> Optional[Path]:
        fn, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "All Supported (*.wav *.iq *.raw *.bin *.sigmf-meta);;WAV Files (*.wav);;Raw IQ (*.iq *.raw *.bin);;All Files (*.*)",
        )
        return Path(fn) if fn else None

    def _load_file(self, path: Path) -> Optional[SignalRecord]:
        try:
            suf = path.suffix.lower()
            if suf == ".wav":
                from signalinsight.io.wav_loader import WavSignalLoader
                return WavSignalLoader().load(path)
            elif "sigmf" in path.name.lower():
                from signalinsight.io.sigmf_loader import SigMFSignalLoader
                return SigMFSignalLoader().load(path)
            else:
                from signalinsight.io.iq_loader import RawIQSignalLoader
                return RawIQSignalLoader().load(path, sample_rate=10e6, center_frequency=0.0, data_type="float32")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Load Error", f"Failed to load comparison signal:\n{e}")
            return None
