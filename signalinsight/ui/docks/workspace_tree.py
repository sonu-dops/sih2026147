"""Left Workspace Explorer tree widget with context menus and double-click navigation."""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QDockWidget, QMenu, QTreeView, QVBoxLayout, QWidget

from signalinsight.core.models import SignalRecord


class WorkspaceExplorerDock(QDockWidget):
    """Hierarchical workspace tree matching professional laboratory software."""

    node_selected = pyqtSignal(str)  # Emits node category/path for view switching

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("WORKSPACE EXPLORER", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self._init_ui()

    def _init_ui(self) -> None:
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.doubleClicked.connect(self._on_item_double_clicked)

        self.model = QStandardItemModel()
        self.tree.setModel(self.model)

        # Build initial structure
        self.root_projects = QStandardItem("PROJECTS")
        self.root_projects.setSelectable(False)
        self.root_projects.setData("projects_root")
        self.model.appendRow(self.root_projects)

        self.active_project_item = QStandardItem("Active Session")
        self.root_projects.appendRow(self.active_project_item)

        self.signals_group = QStandardItem("Signals")
        self.metadata_group = QStandardItem("Metadata")
        self.results_group = QStandardItem("Analysis Results")
        self.reports_group = QStandardItem("Reports")
        self.pipeline_group = QStandardItem("Processing Blocks")

        self.active_project_item.appendRow(self.signals_group)
        self.active_project_item.appendRow(self.metadata_group)
        self.active_project_item.appendRow(self.results_group)
        self.active_project_item.appendRow(self.reports_group)
        self.active_project_item.appendRow(self.pipeline_group)

        # Sub-results nodes
        for r_name in [
            "Time Domain",
            "Frequency Spectrum",
            "Spectrogram",
            "Constellation",
            "Parameter Estimation",
            "Modulation Analysis",
            "Synchronization",
            "Decoding",
        ]:
            item = QStandardItem(r_name)
            item.setData(r_name)
            self.results_group.appendRow(item)

        # Pipeline blocks
        for b_name in ["Filtering", "Resampling", "DC Removal", "Synchronization", "Demodulation", "FEC"]:
            item = QStandardItem(b_name)
            item.setData(b_name)
            self.pipeline_group.appendRow(item)

        self.tree.expandAll()
        self.setWidget(self.tree)

    def set_active_signal(self, signal_rec: SignalRecord) -> None:
        self.signals_group.removeRows(0, self.signals_group.rowCount())
        sig_name = signal_rec.source_file.name if signal_rec.source_file else "Active Signal"
        item = QStandardItem(sig_name)
        item.setData("active_signal")
        self.signals_group.appendRow(item)
        self.tree.expand(self.signals_group.index())

    def _on_item_double_clicked(self, index) -> None:
        item = self.model.itemFromIndex(index)
        if item and item.data():
            self.node_selected.emit(str(item.data()))

    def _show_context_menu(self, pos) -> None:
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        item = self.model.itemFromIndex(index)
        menu = QMenu(self)

        act_open = QAction("Open", self)
        act_open.triggered.connect(lambda: self._on_item_double_clicked(index))
        menu.addAction(act_open)

        menu.addSeparator()
        act_props = QAction("Properties", self)
        menu.addAction(act_props)

        menu.exec(self.tree.viewport().mapToGlobal(pos))
