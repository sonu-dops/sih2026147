"""High-performance Spectrum and Welch PSD visualization widget."""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from signalinsight.core.constants import (
    COLOR_GRID,
    COLOR_PLOT_BG,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    COLOR_TRACE_PSD,
    COLOR_WARNING,
    SUPPORTED_WINDOWS,
)
from signalinsight.core.models import SignalRecord
from signalinsight.dsp.fft import FFTEngine
from signalinsight.dsp.psd import PSDEngine


class SpectrumView(QWidget):
    """Displays windowed FFT spectrum and Welch PSD with peak and bandwidth markers."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.signal_rec: Optional[SignalRecord] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Control strip
        ctrl_layout = QHBoxLayout()

        lbl_mode = QLabel("Mode:")
        lbl_mode.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8.5pt;")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Welch PSD (dBFS/Hz)", "FFT Magnitude (dBFS)", "Linear Magnitude"])
        self.combo_mode.currentIndexChanged.connect(self._recompute_spectrum)

        lbl_win = QLabel("Window:")
        lbl_win.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8.5pt;")
        self.combo_win = QComboBox()
        self.combo_win.addItems(SUPPORTED_WINDOWS)
        self.combo_win.currentIndexChanged.connect(self._recompute_spectrum)

        lbl_fft_size = QLabel("FFT Size:")
        lbl_fft_size.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8.5pt;")
        self.combo_fft_size = QComboBox()
        self.combo_fft_size.addItems(["512", "1024", "2048", "4096", "8192", "16384"])
        self.combo_fft_size.setCurrentText("2048")
        self.combo_fft_size.currentIndexChanged.connect(self._recompute_spectrum)

        self.peak_label = QLabel("Peak: -- Hz, -- dBFS")
        self.peak_label.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold; font-family: monospace; font-size: 8pt;")

        ctrl_layout.addWidget(lbl_mode)
        ctrl_layout.addWidget(self.combo_mode)
        ctrl_layout.addWidget(lbl_win)
        ctrl_layout.addWidget(self.combo_win)
        ctrl_layout.addWidget(lbl_fft_size)
        ctrl_layout.addWidget(self.combo_fft_size)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.peak_label)

        layout.addLayout(ctrl_layout)

        # Plot Widget
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_PLOT_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.5)
        self.plot_widget.setLabel("bottom", "Frequency", units="Hz")
        self.plot_widget.setLabel("left", "Spectral Density", units="dBFS/Hz")

        self.curve_spec = self.plot_widget.plot(pen=pg.mkPen(COLOR_TRACE_PSD, width=1.5))

        # Peak Point Marker
        self.peak_scatter = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(COLOR_WARNING, width=2),
            brush=pg.mkBrush("#ff0000"),
            symbol="t",
        )
        self.plot_widget.addItem(self.peak_scatter)

        # Crosshair lines
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#94a3b8", style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#94a3b8", style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        layout.addWidget(self.plot_widget)

    def set_signal(self, signal_rec: SignalRecord) -> None:
        self.signal_rec = signal_rec
        self._recompute_spectrum()

    def _recompute_spectrum(self) -> None:
        if self.signal_rec is None:
            return

        mode = self.combo_mode.currentText()
        win = self.combo_win.currentText()
        fft_sz = int(self.combo_fft_size.currentText())

        fs = self.signal_rec.sample_rate
        fc = self.signal_rec.center_frequency

        if "Welch" in mode:
            psd_res = PSDEngine.compute_psd(
                self.signal_rec.samples,
                sample_rate=fs,
                nperseg=fft_sz,
                window_name=win,
                center_freq=fc,
            )
            freqs = psd_res.frequencies
            vals = psd_res.psd_db_hz
            self.plot_widget.setLabel("left", "Spectral Density", units="dBFS/Hz")
        else:
            spec_res = FFTEngine.compute_spectrum(
                self.signal_rec.samples,
                sample_rate=fs,
                fft_size=fft_sz,
                window_name=win,
                center_freq=fc,
            )
            freqs = spec_res.frequencies
            if "Linear" in mode:
                vals = spec_res.magnitude
                self.plot_widget.setLabel("left", "Linear Magnitude", units="V")
            else:
                vals = spec_res.power_db
                self.plot_widget.setLabel("left", "Power Spectrum", units="dBFS")

        self.curve_spec.setData(freqs, vals)

        # Highlight maximum peak
        peak_idx = int(np.argmax(vals))
        peak_f = float(freqs[peak_idx])
        peak_v = float(vals[peak_idx])
        self.peak_scatter.setData([{"pos": (peak_f, peak_v), "data": 1}])

        # Format peak text
        if abs(peak_f) >= 1e9:
            f_str = f"{peak_f / 1e9:.6f} GHz"
        elif abs(peak_f) >= 1e6:
            f_str = f"{peak_f / 1e6:.6f} MHz"
        elif abs(peak_f) >= 1e3:
            f_str = f"{peak_f / 1e3:.4f} kHz"
        else:
            f_str = f"{peak_f:.2f} Hz"

        self.peak_label.setText(f"Peak: {f_str} @ {peak_v:.2f} dBFS")

    def _on_mouse_moved(self, pos) -> None:
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self.v_line.setPos(mouse_point.x())
            self.h_line.setPos(mouse_point.y())
