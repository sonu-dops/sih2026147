"""High-performance 2D Spectrogram waterfall view using PyQtGraph."""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from signalinsight.core.constants import COLOR_PLOT_BG, COLOR_TEXT_MUTED
from signalinsight.core.models import SignalRecord
from signalinsight.dsp.spectrogram import SpectrogramEngine


class SpectrogramView(QWidget):
    """2D Time-Frequency Spectrogram with dynamic range and colormap controls."""

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

        lbl_cmap = QLabel("Colormap:")
        lbl_cmap.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8.5pt;")
        self.combo_cmap = QComboBox()
        self.combo_cmap.addItems(["Viridis", "Inferno", "Turbo", "Plasma"])
        self.combo_cmap.currentIndexChanged.connect(self._update_colormap)

        lbl_dr = QLabel("Dynamic Range:")
        lbl_dr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8.5pt;")
        self.slider_dr = QSlider(Qt.Orientation.Horizontal)
        self.slider_dr.setRange(20, 120)
        self.slider_dr.setValue(70)
        self.slider_dr.valueChanged.connect(self._recompute)

        self.dr_val_label = QLabel("70 dB")
        self.dr_val_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: monospace; font-size: 8pt;")
        self.slider_dr.valueChanged.connect(lambda v: self.dr_val_label.setText(f"{v} dB"))

        self.coord_label = QLabel("T: -- s, F: -- Hz")
        self.coord_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: monospace; font-size: 8pt;")

        ctrl_layout.addWidget(lbl_cmap)
        ctrl_layout.addWidget(self.combo_cmap)
        ctrl_layout.addWidget(lbl_dr)
        ctrl_layout.addWidget(self.slider_dr)
        ctrl_layout.addWidget(self.dr_val_label)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.coord_label)

        layout.addLayout(ctrl_layout)

        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_PLOT_BG)
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.setLabel("left", "Frequency", units="Hz")

        # Image Item
        self.img_item = pg.ImageItem()
        self.plot_widget.addItem(self.img_item)

        # Crosshair lines
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#94a3b8", style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#94a3b8", style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        self._update_colormap()
        layout.addWidget(self.plot_widget)

    def set_signal(self, signal_rec: SignalRecord) -> None:
        self.signal_rec = signal_rec
        self._recompute()

    def _recompute(self) -> None:
        if self.signal_rec is None:
            return

        dr = float(self.slider_dr.value())
        spec_res = SpectrogramEngine.compute_spectrogram(
            self.signal_rec.samples,
            sample_rate=self.signal_rec.sample_rate,
            center_freq=self.signal_rec.center_frequency,
            dynamic_range_db=dr,
        )

        t = spec_res.times
        f = spec_res.frequencies
        data = spec_res.spectrogram_db  # [freqs, times]

        # In pyqtgraph, ImageItem shape is [x, y] = [time, freq]
        # Transpose data so x=time, y=freq
        img_data = data.T

        self.img_item.setImage(img_data)

        # Scale image to map pixel coordinates to real-world time & frequency
        t_min, t_max = t[0], t[-1] if len(t) > 1 else 1.0
        f_min, f_max = f[0], f[-1] if len(f) > 1 else 1.0

        t_scale = (t_max - t_min) / max(1, len(t))
        f_scale = (f_max - f_min) / max(1, len(f))

        self.img_item.setRect(pg.QtCore.QRectF(t_min, f_min, t_max - t_min, f_max - f_min))
        self.plot_widget.autoRange()

    def _update_colormap(self) -> None:
        cmap_name = self.combo_cmap.currentText().lower()
        cmap = pg.colormap.get(cmap_name)
        if cmap:
            lut = cmap.getLookupTable(0.0, 1.0, 256)
            self.img_item.setLookupTable(lut)

    def _on_mouse_moved(self, pos) -> None:
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_t = mouse_point.x()
            y_f = mouse_point.y()
            self.v_line.setPos(x_t)
            self.h_line.setPos(y_f)

            if abs(y_f) >= 1e9:
                f_str = f"{y_f / 1e9:.6f} GHz"
            elif abs(y_f) >= 1e6:
                f_str = f"{y_f / 1e6:.6f} MHz"
            elif abs(y_f) >= 1e3:
                f_str = f"{y_f / 1e3:.3f} kHz"
            else:
                f_str = f"{y_f:.1f} Hz"

            self.coord_label.setText(f"T: {x_t:.4f} s, F: {f_str}")
