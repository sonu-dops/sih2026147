"""Marker management dock widget."""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.models import Marker, MarkerType


class MarkersDock(QDockWidget):
    """Interactive marker manager supporting peak, delta, and frequency/time markers."""

    marker_added = pyqtSignal(object)  # Marker
    marker_removed = pyqtSignal(str)   # marker_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("MARKERS", parent)
        self.markers: List[Marker] = []
        self._init_ui()

    def _init_ui(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Action bar
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Marker")
        self.btn_add.clicked.connect(self._add_default_marker)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self._remove_selected)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Type", "Position", "Value", "Plot"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.setWidget(content)

    def add_marker(self, marker: Marker) -> None:
        self.markers.append(marker)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(marker.id))
        self.table.setItem(row, 1, QTableWidgetItem(marker.marker_type.value))
        self.table.setItem(row, 2, QTableWidgetItem(f"{marker.position:,.3f}"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{marker.value:,.2f} {marker.units}"))
        self.table.setItem(row, 4, QTableWidgetItem(marker.source_plot))
        self.marker_added.emit(marker)

    def _add_default_marker(self) -> None:
        idx = len(self.markers) + 1
        m = Marker(
            id=f"M{idx}",
            marker_type=MarkerType.PEAK,
            position=0.0,
            value=0.0,
            units="dBFS",
            source_plot="Spectrum",
        )
        self.add_marker(m)

    def _remove_selected(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self.markers):
            marker = self.markers.pop(row)
            self.table.removeRow(row)
            self.marker_removed.emit(marker.id)

    def clear_all(self) -> None:
        self.markers.clear()
        self.table.setRowCount(0)
