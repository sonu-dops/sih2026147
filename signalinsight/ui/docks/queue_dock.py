"""Batch processing queue monitor dock."""

from typing import Optional
from PyQt6.QtCore import Qt
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


class QueueDock(QDockWidget):
    """Monitors multi-file batch analysis queue."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("PROCESSING QUEUE", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)
        self._init_ui()

    def _init_ui(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Action Buttons
        act_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Queue")
        self.btn_pause = QPushButton("Pause")
        self.btn_clear = QPushButton("Clear Completed")
        act_layout.addWidget(self.btn_start)
        act_layout.addWidget(self.btn_pause)
        act_layout.addStretch()
        act_layout.addWidget(self.btn_clear)
        layout.addLayout(act_layout)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["File", "Status", "Progress", "Stage", "Elapsed", "Result"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setMinimumHeight(120)
        layout.addWidget(self.table)

        self.setWidget(content)

    def add_queue_item(self, filename: str) -> int:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(filename))
        self.table.setItem(row, 1, QTableWidgetItem("Queued"))
        self.table.setItem(row, 2, QTableWidgetItem("0%"))
        self.table.setItem(row, 3, QTableWidgetItem("Pending"))
        self.table.setItem(row, 4, QTableWidgetItem("0.0s"))
        self.table.setItem(row, 5, QTableWidgetItem("--"))
        return row

    def update_queue_item(self, row: int, status: str, progress_pct: int, stage: str, result_summary: str = "") -> None:
        if 0 <= row < self.table.rowCount():
            self.table.setItem(row, 1, QTableWidgetItem(status))
            self.table.setItem(row, 2, QTableWidgetItem(f"{progress_pct}%"))
            self.table.setItem(row, 3, QTableWidgetItem(stage))
            if result_summary:
                self.table.setItem(row, 5, QTableWidgetItem(result_summary))
