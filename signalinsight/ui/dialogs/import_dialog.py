"""Raw IQ and WAV File Import Configuration Dialog."""

from pathlib import Path
from typing import Any, Dict, Optional
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import COLOR_PLOT_BG, COLOR_TRACE_I, COLOR_TRACE_Q
from signalinsight.core.models import SignalRecord
from signalinsight.io.iq_loader import RawIQSignalLoader


class FileImportDialog(QDialog):
    """Configures raw IQ binary or WAV file import parameters with live preview."""

    def __init__(self, filepath: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.filepath = Path(filepath)
        self.imported_record: Optional[SignalRecord] = None
        self.setWindowTitle(f"File Import Configuration — {self.filepath.name}")
        self.resize(750, 500)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)

        # Left Parameters Column
        left_layout = QVBoxLayout()

        grp_params = QGroupBox("FORMAT & PHYSICAL PARAMETERS")
        form = QFormLayout(grp_params)

        self.combo_dtype = QComboBox()
        self.combo_dtype.addItems(["float32", "int16", "uint8", "int8", "int32", "float64"])
        form.addRow("Data Type:", self.combo_dtype)

        self.combo_iq_order = QComboBox()
        self.combo_iq_order.addItems(["IQ", "QI"])
        form.addRow("IQ Ordering:", self.combo_iq_order)

        self.combo_channel_mode = QComboBox()
        self.combo_channel_mode.addItems(["Complex (Interleaved)", "Real Only"])
        form.addRow("Channel Mode:", self.combo_channel_mode)

        self.combo_endian = QComboBox()
        self.combo_endian.addItems(["Little Endian", "Big Endian"])
        form.addRow("Endianness:", self.combo_endian)

        # Sample Rate
        sr_layout = QHBoxLayout()
        self.spin_sr = QDoubleSpinBox()
        self.spin_sr.setRange(0.001, 100000.0)
        self.spin_sr.setValue(10.0)
        self.spin_sr.setDecimals(4)
        self.combo_sr_unit = QComboBox()
        self.combo_sr_unit.addItems(["Msps", "ksps", "sps", "Gsps"])
        sr_layout.addWidget(self.spin_sr)
        sr_layout.addWidget(self.combo_sr_unit)
        form.addRow("Sample Rate:", sr_layout)

        # Center Frequency
        fc_layout = QHBoxLayout()
        self.spin_fc = QDoubleSpinBox()
        self.spin_fc.setRange(0.0, 100000.0)
        self.spin_fc.setValue(2.4)
        self.spin_fc.setDecimals(4)
        self.combo_fc_unit = QComboBox()
        self.combo_fc_unit.addItems(["GHz", "MHz", "kHz", "Hz"])
        fc_layout.addWidget(self.spin_fc)
        fc_layout.addWidget(self.combo_fc_unit)
        form.addRow("Center Frequency:", fc_layout)

        self.spin_offset_bytes = QSpinBox()
        self.spin_offset_bytes.setRange(0, 100000000)
        self.spin_offset_bytes.setValue(0)
        form.addRow("Byte Offset:", self.spin_offset_bytes)

        left_layout.addWidget(grp_params)

        btn_preview = QPushButton("Preview Slice")
        btn_preview.clicked.connect(self._preview_slice)
        left_layout.addWidget(btn_preview)

        left_layout.addStretch()

        # Action buttons
        btn_row = QHBoxLayout()
        self.btn_import = QPushButton("Import Signal")
        self.btn_import.setObjectName("primary_action")
        self.btn_import.clicked.connect(self._do_import)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_import)
        btn_row.addWidget(btn_cancel)
        left_layout.addLayout(btn_row)

        main_layout.addLayout(left_layout, stretch=1)

        # Right Preview Plot
        right_layout = QVBoxLayout()
        lbl_prev = QLabel("REAL-TIME PREVIEW (First 2,000 samples)")
        lbl_prev.setStyleSheet("color: #64748b; font-weight: bold; font-size: 8pt;")
        right_layout.addWidget(lbl_prev)

        self.preview_plot = pg.PlotWidget()
        self.preview_plot.setBackground(COLOR_PLOT_BG)
        self.preview_plot.showGrid(x=True, y=True, alpha=0.5)
        self.curve_i = self.preview_plot.plot(pen=pg.mkPen(COLOR_TRACE_I, width=1.5), name="I")
        self.curve_q = self.preview_plot.plot(pen=pg.mkPen(COLOR_TRACE_Q, width=1.5), name="Q")
        right_layout.addWidget(self.preview_plot)

        main_layout.addLayout(right_layout, stretch=1)

        # Trigger initial preview
        self._preview_slice()

    def _get_fs_hz(self) -> float:
        val = self.spin_sr.value()
        unit = self.combo_sr_unit.currentText()
        mult = {"sps": 1.0, "ksps": 1e3, "Msps": 1e6, "Gsps": 1e9}[unit]
        return val * mult

    def _get_fc_hz(self) -> float:
        val = self.spin_fc.value()
        unit = self.combo_fc_unit.currentText()
        mult = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9}[unit]
        return val * mult

    def _preview_slice(self) -> None:
        try:
            loader = RawIQSignalLoader()
            fs = self._get_fs_hz()
            fc = self._get_fc_hz()
            is_complex = "Complex" in self.combo_channel_mode.currentText()

            rec = loader.load(
                filepath=self.filepath,
                sample_rate=fs,
                center_frequency=fc,
                data_type=self.combo_dtype.currentText(),
                iq_order=self.combo_iq_order.currentText(),
                channel_mode="Complex" if is_complex else "Real",
                endianness=self.combo_endian.currentText(),
                offset_bytes=self.spin_offset_bytes.value(),
                max_samples=2000,
            )

            samples = rec.samples
            t = [i / fs for i in range(len(samples))]
            if rec.is_complex:
                self.curve_i.setData(t, samples.real)
                self.curve_q.setData(t, samples.imag)
            else:
                self.curve_i.setData(t, samples)
                self.curve_q.setData([], [])
            self.preview_plot.autoRange()
        except Exception as e:
            self.curve_i.setData([], [])
            self.curve_q.setData([], [])

    def _do_import(self) -> None:
        loader = RawIQSignalLoader()
        fs = self._get_fs_hz()
        fc = self._get_fc_hz()
        is_complex = "Complex" in self.combo_channel_mode.currentText()

        self.imported_record = loader.load(
            filepath=self.filepath,
            sample_rate=fs,
            center_frequency=fc,
            data_type=self.combo_dtype.currentText(),
            iq_order=self.combo_iq_order.currentText(),
            channel_mode="Complex" if is_complex else "Real",
            endianness=self.combo_endian.currentText(),
            offset_bytes=self.spin_offset_bytes.value(),
        )
        self.accept()
