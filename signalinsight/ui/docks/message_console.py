"""Bottom Message & Audit Log console dock."""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import COLOR_ERROR, COLOR_SUCCESS, COLOR_WARNING
from signalinsight.core.logging import LogEntry, logger


class MessageConsoleDock(QDockWidget):
    """Real-time structured logging console with severity filters and auto-scroll."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("MESSAGE / LOG CONSOLE", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)
        self._all_entries: List[LogEntry] = []
        self._init_ui()
        logger.add_listener(self._on_log_entry)

    def _init_ui(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Filter toolbar
        bar_layout = QHBoxLayout()
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["ALL LEVELS", "INFO & HIGHER", "WARNING & HIGHER", "ERRORS ONLY"])
        self.combo_filter.currentIndexChanged.connect(self._rebuild_console_text)

        self.chk_autoscroll = QCheckBox("Auto-Scroll")
        self.chk_autoscroll.setChecked(True)

        self.btn_clear = QPushButton("Clear Log")
        self.btn_clear.clicked.connect(self.clear_log)

        bar_layout.addWidget(self.combo_filter)
        bar_layout.addWidget(self.chk_autoscroll)
        bar_layout.addStretch()
        bar_layout.addWidget(self.btn_clear)
        layout.addLayout(bar_layout)

        # Log Display
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            "background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; font-family: 'Consolas', 'Courier New', monospace; font-size: 8.5pt;"
        )
        layout.addWidget(self.text_edit)

        self.setWidget(content)

    def _on_log_entry(self, entry: LogEntry) -> None:
        self._all_entries.append(entry)
        if self._matches_filter(entry):
            self._append_entry(entry)

    def _matches_filter(self, entry: LogEntry) -> bool:
        filt = self.combo_filter.currentText()
        lvl = entry.level.upper()
        if filt == "ALL LEVELS":
            return True
        elif filt == "INFO & HIGHER":
            return lvl in ("INFO", "WARNING", "ERROR", "CRITICAL")
        elif filt == "WARNING & HIGHER":
            return lvl in ("WARNING", "ERROR", "CRITICAL")
        elif filt == "ERRORS ONLY":
            return lvl in ("ERROR", "CRITICAL")
        return True

    def _append_entry(self, entry: LogEntry) -> None:
        self.text_edit.appendPlainText(entry.formatted_line())
        if self.chk_autoscroll.isChecked():
            sb = self.text_edit.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _rebuild_console_text(self) -> None:
        self.text_edit.clear()
        for entry in self._all_entries:
            if self._matches_filter(entry):
                self.text_edit.appendPlainText(entry.formatted_line())
        if self.chk_autoscroll.isChecked():
            sb = self.text_edit.verticalScrollBar()
            sb.setValue(sb.maximum())

    def clear_log(self) -> None:
        self._all_entries.clear()
        self.text_edit.clear()
        logger.clear()
