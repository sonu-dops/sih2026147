"""Properties Inspector dock displaying detailed signal and node attributes."""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from signalinsight.core.models import SignalRecord


class PropertiesDock(QDockWidget):
    """Shows technical metadata and physical parameters with provenance tags."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("PROPERTIES", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self._init_ui()

    def _init_ui(self) -> None:
        self.table = QTableWidget(12, 2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        props = [
            "File Name",
            "Format",
            "Data Type",
            "Channel Mode",
            "IQ Ordering",
            "Sample Rate",
            "Center Frequency",
            "Sample Count",
            "Duration",
            "Timestamp",
            "File Size",
            "Metadata Source",
        ]
        for row, p in enumerate(props):
            self.table.setItem(row, 0, QTableWidgetItem(p))
            self.table.setItem(row, 1, QTableWidgetItem("N/A"))

        self.setWidget(self.table)

    def set_signal(self, signal_rec: SignalRecord) -> None:
        sr_src = signal_rec.metadata_sources.get("sample_rate")
        fc_src = signal_rec.metadata_sources.get("center_frequency")

        sr_tag = f" [{sr_src.value}]" if sr_src else ""
        fc_tag = f" [{fc_src.value}]" if fc_src else ""

        sr_str = f"{signal_rec.sample_rate / 1e6:.4f} Msps{sr_tag}" if signal_rec.sample_rate >= 1e6 else f"{signal_rec.sample_rate:,.1f} Hz{sr_tag}"

        if signal_rec.center_frequency >= 1e9:
            fc_str = f"{signal_rec.center_frequency / 1e9:.6f} GHz{fc_tag}"
        elif signal_rec.center_frequency >= 1e6:
            fc_str = f"{signal_rec.center_frequency / 1e6:.4f} MHz{fc_tag}"
        else:
            fc_str = f"{signal_rec.center_frequency:,.1f} Hz{fc_tag}"

        file_sz = "N/A"
        if signal_rec.source_file and signal_rec.source_file.exists():
            sz = signal_rec.source_file.stat().st_size
            if sz > 1024**3:
                file_sz = f"{sz / (1024**3):.2f} GB"
            elif sz > 1024**2:
                file_sz = f"{sz / (1024**2):.2f} MB"
            else:
                file_sz = f"{sz / 1024:.1f} KB"

        vals = [
            signal_rec.source_file.name if signal_rec.source_file else "Virtual Buffer",
            signal_rec.metadata.get("original_dtype", signal_rec.data_type),
            signal_rec.data_type,
            "Complex (I + jQ)" if signal_rec.is_complex else "Real Baseband",
            signal_rec.iq_order,
            sr_str,
            fc_str,
            f"{signal_rec.sample_count:,} samples",
            f"{signal_rec.duration:.4f} s",
            signal_rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            file_sz,
            "SigMF" if "SigMF" in signal_rec.metadata.get("format", "") else "User / Header",
        ]

        for row, v in enumerate(vals):
            self.table.setItem(row, 1, QTableWidgetItem(v))
