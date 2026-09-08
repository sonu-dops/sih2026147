"""High-performance Time Domain visualization widget using PyQtGraph."""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from signalinsight.core.constants import (
    COLOR_GRID,
    COLOR_PLOT_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    COLOR_TRACE_FREQ,
    COLOR_TRACE_I,
    COLOR_TRACE_MAG,
    COLOR_TRACE_PHASE,
    COLOR_TRACE_Q,
)
from signalinsight.core.models import SignalRecord
from signalinsight.dsp.analytic import AnalyticSignalEngine


class TimeDomainView(QWidget):
    """Displays I, Q, Magnitude, Envelope, Phase, and Instantaneous Frequency with high-performance decimation."""

    marker_requested = pyqtSignal(float, float)  # time, value

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.signal_rec: Optional[SignalRecord] = None
        self._dec_samples: Optional[np.ndarray] = None
        self._dec_t: Optional[np.ndarray] = None
        self._dec_fs: float = 1.0
        self._f_inst_computed: bool = False

        # 60 FPS Crosshair throttler
        self._mouse_timer = QTimer(self)
        self._mouse_timer.setSingleShot(True)
        self._mouse_timer.setInterval(16)
        self._mouse_timer.timeout.connect(self._process_mouse_move)
        self._pending_mouse_pos = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Control strip (trace toggles)
        ctrl_layout = QHBoxLayout()
        self.chk_i = QCheckBox("I (In-Phase)")
        self.chk_i.setChecked(True)
        self.chk_i.setStyleSheet(f"color: {COLOR_TRACE_I}; font-weight: bold;")
        self.chk_i.toggled.connect(self._update_visibility)

        self.chk_q = QCheckBox("Q (Quadrature)")
        self.chk_q.setChecked(True)
        self.chk_q.setStyleSheet(f"color: {COLOR_TRACE_Q}; font-weight: bold;")
        self.chk_q.toggled.connect(self._update_visibility)

        self.chk_mag = QCheckBox("Magnitude |x|")
        self.chk_mag.setChecked(False)
        self.chk_mag.setStyleSheet(f"color: {COLOR_TRACE_MAG}; font-weight: bold;")
        self.chk_mag.toggled.connect(self._update_visibility)

        self.chk_f_inst = QCheckBox("Inst Freq")
        self.chk_f_inst.setChecked(False)
        self.chk_f_inst.setStyleSheet(f"color: {COLOR_TRACE_FREQ}; font-weight: bold;")
        self.chk_f_inst.toggled.connect(self._on_f_inst_toggled)

        self.cursor_label = QLabel("Cursor: -- s, -- V")
        self.cursor_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: monospace; font-size: 8pt;")

        ctrl_layout.addWidget(self.chk_i)
        ctrl_layout.addWidget(self.chk_q)
        ctrl_layout.addWidget(self.chk_mag)
        ctrl_layout.addWidget(self.chk_f_inst)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.cursor_label)

        layout.addLayout(ctrl_layout)

        # Plot Widget — Fast rendering configuration
        pg.setConfigOptions(antialias=False, enableExperimental=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_PLOT_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.5)
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.setLabel("left", "Amplitude", units="V / FS")

        # Plot Curves with hardware-efficient peak downsampling & view clipping
        self.curve_i = self.plot_widget.plot(pen=pg.mkPen(COLOR_TRACE_I, width=1.5), name="I")
        self.curve_q = self.plot_widget.plot(pen=pg.mkPen(COLOR_TRACE_Q, width=1.5), name="Q")
        self.curve_mag = self.plot_widget.plot(pen=pg.mkPen(COLOR_TRACE_MAG, width=1.5), name="Mag")
        self.curve_f_inst = self.plot_widget.plot(pen=pg.mkPen(COLOR_TRACE_FREQ, width=1.5), name="Freq")

        for curve in (self.curve_i, self.curve_q, self.curve_mag, self.curve_f_inst):
            curve.setDownsampling(auto=True, method="peak")
            curve.setClipToView(True)

        # Crosshair Lines
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#94a3b8", style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#94a3b8", style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        layout.addWidget(self.plot_widget)

    def set_signal(self, signal_rec: SignalRecord, max_display_points: int = 10000) -> None:
        """Renders the signal in time domain with level-of-detail decimation."""
        self.signal_rec = signal_rec
        samples = signal_rec.samples
        fs = signal_rec.sample_rate
        n = len(samples)

        # Level-of-detail decimation (10,000 points provides multiple data points per screen pixel)
        if n > max_display_points:
            step = n // max_display_points
            dec_samples = samples[::step]
            t = np.arange(0, n, step) / fs
        else:
            step = 1
            dec_samples = samples
            t = np.arange(n) / fs

        self._dec_samples = dec_samples
        self._dec_t = t
        self._dec_fs = fs / step
        self._f_inst_computed = False

        # I and Q
        if np.iscomplexobj(dec_samples):
            self.curve_i.setData(t, dec_samples.real)
            self.curve_q.setData(t, dec_samples.imag)
            self.chk_q.setEnabled(True)
        else:
            self.curve_i.setData(t, dec_samples)
            self.curve_q.setData([], [])
            self.chk_q.setEnabled(False)

        # Magnitude
        mag = np.abs(dec_samples)
        self.curve_mag.setData(t, mag)

        # Lazy instantaneous frequency (only computed if checkbox is active)
        if self.chk_f_inst.isChecked():
            self._compute_and_set_inst_freq()
        else:
            self.curve_f_inst.setData([], [])

        self.plot_widget.autoRange()
        self._update_visibility()

    def _on_f_inst_toggled(self, checked: bool) -> None:
        if checked and not self._f_inst_computed:
            self._compute_and_set_inst_freq()
        self._update_visibility()

    def _compute_and_set_inst_freq(self) -> None:
        if self._dec_samples is None or self._dec_t is None:
            return
        try:
            props = AnalyticSignalEngine.compute_properties(self._dec_samples, sample_rate=self._dec_fs)
            self.curve_f_inst.setData(self._dec_t, props.instantaneous_frequency)
            self._f_inst_computed = True
        except Exception:
            self.curve_f_inst.setData([], [])

    def _update_visibility(self) -> None:
        self.curve_i.setVisible(self.chk_i.isChecked())
        self.curve_q.setVisible(self.chk_q.isChecked() and self.chk_q.isEnabled())
        self.curve_mag.setVisible(self.chk_mag.isChecked())
        self.curve_f_inst.setVisible(self.chk_f_inst.isChecked())

    def _on_mouse_moved(self, pos) -> None:
        self._pending_mouse_pos = pos
        if not self._mouse_timer.isActive():
            self._mouse_timer.start()

    def _process_mouse_move(self) -> None:
        if self._pending_mouse_pos is None:
            return
        pos = self._pending_mouse_pos
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()
            self.v_line.setPos(x_val)
            self.h_line.setPos(y_val)

            # Engineering notation format
            if abs(x_val) < 1e-3:
                t_str = f"{x_val * 1e6:.2f} µs"
            elif abs(x_val) < 1.0:
                t_str = f"{x_val * 1e3:.2f} ms"
            else:
                t_str = f"{x_val:.4f} s"

            self.cursor_label.setText(f"Cursor: {t_str}, {y_val:.4f} V")
