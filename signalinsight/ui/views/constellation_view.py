"""High-performance Constellation and EVM analysis view using PyQtGraph."""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from signalinsight.core.constants import (
    COLOR_CONSTELLATION,
    COLOR_CONSTELLATION_IDEAL,
    COLOR_PLOT_BG,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_WARNING,
)
from signalinsight.core.models import DemodulationResult
from signalinsight.demodulation.constellation import ConstellationAnalyzer
from signalinsight.demodulation.psk import QPSKDemodulator


class ConstellationView(QWidget):
    """Displays I/Q constellation scatter plot, ideal reference points, and EVM metrics."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.symbols: Optional[np.ndarray] = None
        self.ideal_symbols: Optional[np.ndarray] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Control Strip
        ctrl_layout = QHBoxLayout()

        self.chk_ideal = QCheckBox("Show Ideal Points")
        self.chk_ideal.setChecked(True)
        self.chk_ideal.setStyleSheet(f"color: {COLOR_CONSTELLATION_IDEAL}; font-weight: bold;")
        self.chk_ideal.toggled.connect(self._update_visibility)

        self.chk_grid = QCheckBox("Decision Crosshairs")
        self.chk_grid.setChecked(True)
        self.chk_grid.toggled.connect(self._update_visibility)

        lbl_pts = QLabel("Symbol Limit:")
        lbl_pts.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8.5pt;")
        self.combo_pts = QComboBox()
        self.combo_pts.addItems(["500", "1000", "2000", "5000", "All"])
        self.combo_pts.setCurrentText("1000")
        self.combo_pts.currentIndexChanged.connect(self._redraw_points)

        self.evm_label = QLabel("EVM RMS: -- % | Peak: -- %")
        self.evm_label.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-family: monospace; font-weight: bold; font-size: 8.5pt;")

        ctrl_layout.addWidget(self.chk_ideal)
        ctrl_layout.addWidget(self.chk_grid)
        ctrl_layout.addWidget(lbl_pts)
        ctrl_layout.addWidget(self.combo_pts)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.evm_label)

        layout.addLayout(ctrl_layout)

        # Plot Widget
        pg.setConfigOptions(antialias=False, enableExperimental=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_PLOT_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.5)
        self.plot_widget.setLabel("bottom", "In-Phase (I)", units="Norm")
        self.plot_widget.setLabel("left", "Quadrature (Q)", units="Norm")
        self.plot_widget.setAspectLocked(True)

        # Zero-axes crosshairs
        self.axis_v = pg.InfiniteLine(angle=90, pen=pg.mkPen("#cbd5e1", width=1.5))
        self.axis_h = pg.InfiniteLine(angle=0, pen=pg.mkPen("#cbd5e1", width=1.5))
        self.plot_widget.addItem(self.axis_v)
        self.plot_widget.addItem(self.axis_h)

        # Received Scatter Points (useCache=True prevents re-rendering point glyphs)
        self.scatter_received = pg.ScatterPlotItem(
            size=5,
            pen=None,
            brush=pg.mkBrush(COLOR_CONSTELLATION),
            symbol="o",
            pxMode=True,
            useCache=True,
        )
        self.plot_widget.addItem(self.scatter_received)

        # Ideal Reference Scatter Points
        self.scatter_ideal = pg.ScatterPlotItem(
            size=12,
            pen=pg.mkPen(COLOR_CONSTELLATION_IDEAL, width=2),
            brush=pg.mkBrush(0, 0, 0, 0),
            symbol="+",
            pxMode=True,
            useCache=True,
        )
        self.plot_widget.addItem(self.scatter_ideal)

        layout.addWidget(self.plot_widget)

    def set_demod_result(self, demod_result: DemodulationResult, ideal_constellation: Optional[np.ndarray] = None) -> None:
        if demod_result and demod_result.symbols:
            self.symbols = np.array(demod_result.symbols, dtype=np.complex64)
            self.ideal_symbols = ideal_constellation
            if demod_result.evm_rms_pct and demod_result.evm_rms_pct.value is not None:
                evm_rms = demod_result.evm_rms_pct.value
                peak_str = f"{demod_result.evm_peak_pct.value:.2f}%" if demod_result.evm_peak_pct else "N/A"
                self.evm_label.setText(f"EVM RMS: {evm_rms:.2f}% [{demod_result.evm_rms_pct.quality.value}] | Peak: {peak_str}")
            else:
                self.evm_label.setText("EVM: Unsynchronized / N/A")
        else:
            self.symbols = None
            self.ideal_symbols = None
            self.evm_label.setText("EVM RMS: -- %")

        self._redraw_points()

    def set_raw_symbols(self, symbols: np.ndarray, ideal_constellation: Optional[np.ndarray] = None) -> None:
        self.symbols = symbols
        self.ideal_symbols = ideal_constellation
        self._redraw_points()

    def _redraw_points(self) -> None:
        if self.symbols is None or len(self.symbols) == 0:
            self.scatter_received.setData([])
            self.scatter_ideal.setData([])
            return

        lim_str = self.combo_pts.currentText()
        if lim_str == "All":
            sub_syms = self.symbols[:5000]
        else:
            try:
                lim = min(int(lim_str), 5000)
            except ValueError:
                lim = 1000
            sub_syms = self.symbols[:lim]

        # Normalize received symbols to average unit power for standard constellation display
        p_avg = np.mean(np.abs(sub_syms) ** 2)
        norm_syms = sub_syms / np.sqrt(max(p_avg, 1e-12))

        # Vectorized safe float arrays for pyqtgraph
        x_pts = np.nan_to_num(np.asarray(norm_syms.real, dtype=np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
        y_pts = np.nan_to_num(np.asarray(norm_syms.imag, dtype=np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
        self.scatter_received.setData(x=x_pts, y=y_pts)

        # Ideal reference points
        if self.ideal_symbols is not None and len(self.ideal_symbols) > 0:
            p_ideal = np.mean(np.abs(self.ideal_symbols) ** 2)
            norm_ideal = self.ideal_symbols / np.sqrt(max(p_ideal, 1e-12))
            ix_pts = np.nan_to_num(np.asarray(norm_ideal.real, dtype=np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
            iy_pts = np.nan_to_num(np.asarray(norm_ideal.imag, dtype=np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
            self.scatter_ideal.setData(x=ix_pts, y=iy_pts)
        else:
            self.scatter_ideal.setData(x=np.array([], dtype=np.float32), y=np.array([], dtype=np.float32))

        self.plot_widget.setXRange(-2.0, 2.0)
        self.plot_widget.setYRange(-2.0, 2.0)
        self._update_visibility()

    def _update_visibility(self) -> None:
        self.scatter_ideal.setVisible(self.chk_ideal.isChecked())
        self.axis_v.setVisible(self.chk_grid.isChecked())
        self.axis_h.setVisible(self.chk_grid.isChecked())
