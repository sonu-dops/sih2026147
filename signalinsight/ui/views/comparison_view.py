"""Signal comparison mode: side-by-side inspection of two RF recordings."""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
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

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        pg.setConfigOptions(antialias=False, enableExperimental=True)
        splitter = QSplitter()

        # Left Panel (Signal A)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_sig_a = QLabel("Signal A: (None loaded)")
        self.lbl_sig_a.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-weight: bold;")
        self.plot_a_time = pg.PlotWidget()
        self.plot_a_time.setBackground(COLOR_PLOT_BG)
        self.plot_a_time.showGrid(x=True, y=True, alpha=0.5)
        self.plot_a_time.setLabel("bottom", "Time", units="s")
        self.plot_a_spec = pg.PlotWidget()
        self.plot_a_spec.setBackground(COLOR_PLOT_BG)
        self.plot_a_spec.showGrid(x=True, y=True, alpha=0.5)
        self.plot_a_spec.setLabel("bottom", "Frequency", units="Hz")
        left_layout.addWidget(self.lbl_sig_a)
        left_layout.addWidget(self.plot_a_time)
        left_layout.addWidget(self.plot_a_spec)
        splitter.addWidget(left_widget)

        # Right Panel (Signal B)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_sig_b = QLabel("Signal B: (None loaded)")
        self.lbl_sig_b.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold;")
        self.plot_b_time = pg.PlotWidget()
        self.plot_b_time.setBackground(COLOR_PLOT_BG)
        self.plot_b_time.showGrid(x=True, y=True, alpha=0.5)
        self.plot_b_time.setLabel("bottom", "Time", units="s")
        self.plot_b_spec = pg.PlotWidget()
        self.plot_b_spec.setBackground(COLOR_PLOT_BG)
        self.plot_b_spec.showGrid(x=True, y=True, alpha=0.5)
        self.plot_b_spec.setLabel("bottom", "Frequency", units="Hz")
        right_layout.addWidget(self.lbl_sig_b)
        right_layout.addWidget(self.plot_b_time)
        right_layout.addWidget(self.plot_b_spec)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter, stretch=2)

        # Bottom Comparison Metrics Table
        self.metrics_table = QTableWidget(7, 3)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Signal A", "Signal B"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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

    def set_signals(
        self,
        sig_a: SignalRecord,
        res_a: Optional[AnalysisResult],
        sig_b: SignalRecord,
        res_b: Optional[AnalysisResult],
    ) -> None:
        # Update A
        self.lbl_sig_a.setText(f"Signal A: {sig_a.source_file.name if sig_a.source_file else 'Record A'}")
        t_a = np.arange(min(len(sig_a.samples), 5000)) / sig_a.sample_rate
        s_a = sig_a.samples[: len(t_a)]
        self.plot_a_time.clear()
        c_at = self.plot_a_time.plot(t_a, s_a.real, pen=COLOR_PRIMARY_ACCENT)
        c_at.setDownsampling(auto=True, method="peak")
        c_at.setClipToView(True)

        spec_a = FFTEngine.compute_spectrum(sig_a.samples, sample_rate=sig_a.sample_rate, fft_size=2048)
        self.plot_a_spec.clear()
        c_as = self.plot_a_spec.plot(spec_a.frequencies, spec_a.power_db, pen=COLOR_PRIMARY_ACCENT)
        c_as.setDownsampling(auto=True, method="peak")
        c_as.setClipToView(True)

        # Update B
        self.lbl_sig_b.setText(f"Signal B: {sig_b.source_file.name if sig_b.source_file else 'Record B'}")
        t_b = np.arange(min(len(sig_b.samples), 5000)) / sig_b.sample_rate
        s_b = sig_b.samples[: len(t_b)]
        self.plot_b_time.clear()
        c_bt = self.plot_b_time.plot(t_b, s_b.real, pen=COLOR_WARNING)
        c_bt.setDownsampling(auto=True, method="peak")
        c_bt.setClipToView(True)

        spec_b = FFTEngine.compute_spectrum(sig_b.samples, sample_rate=sig_b.sample_rate, fft_size=2048)
        self.plot_b_spec.clear()
        c_bs = self.plot_b_spec.plot(spec_b.frequencies, spec_b.power_db, pen=COLOR_WARNING)
        c_bs.setDownsampling(auto=True, method="peak")
        c_bs.setClipToView(True)

        # Fill table
        if res_a:
            self._fill_col(1, res_a)
        if res_b:
            self._fill_col(2, res_b)

    def _fill_col(self, col: int, res: AnalysisResult) -> None:
        mod_str = res.modulation_result.predicted_modulation if res.modulation_result else "N/A"
        conf_str = f"{res.modulation_result.confidence*100:.1f}%" if res.modulation_result else "N/A"
        cf_str = f"{res.carrier_frequency.value:,.1f} Hz" if res.carrier_frequency.value is not None else "N/A"
        sr_str = f"{res.symbol_rate.value:,.1f} Baud" if res.symbol_rate.value is not None else "N/A"
        obw_str = f"{res.occupied_bw_99.value:,.1f} Hz" if res.occupied_bw_99.value is not None else "N/A"
        snr_str = f"{res.snr_db.value:.2f} dB" if res.snr_db.value is not None else "N/A"
        evm_str = f"{res.demodulation_result.evm_rms_pct.value:.2f}%" if res.demodulation_result and res.demodulation_result.evm_rms_pct else "N/A"

        vals = [mod_str, conf_str, cf_str, sr_str, obw_str, snr_str, evm_str]
        for row, v in enumerate(vals):
            self.metrics_table.setItem(row, col, QTableWidgetItem(v))
