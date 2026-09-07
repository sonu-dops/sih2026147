"""Dockable panels for SignalInsight."""

from signalinsight.ui.docks.workspace_tree import WorkspaceExplorerDock
from signalinsight.ui.docks.properties_dock import PropertiesDock
from signalinsight.ui.docks.analysis_control import AnalysisControlDock
from signalinsight.ui.docks.results_dock import ResultsSummaryDock
from signalinsight.ui.docks.markers_dock import MarkersDock
from signalinsight.ui.docks.message_console import MessageConsoleDock
from signalinsight.ui.docks.queue_dock import QueueDock

__all__ = [
    "WorkspaceExplorerDock",
    "PropertiesDock",
    "AnalysisControlDock",
    "ResultsSummaryDock",
    "MarkersDock",
    "MessageConsoleDock",
    "QueueDock",
]
