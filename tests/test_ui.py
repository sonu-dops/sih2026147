"""Unit tests for desktop UI instantiation and state machine integration."""

import os
import pytest
from PyQt6.QtWidgets import QApplication

from signalinsight.amc.synthetic import SyntheticSignalGenerator
from signalinsight.core.state import AppState
from signalinsight.ui.app import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_init(qapp):
    window = MainWindow()
    assert window.windowTitle().startswith("SIGNALINSIGHT")
    assert window.state_machine.current_state == AppState.EMPTY

    # Load synthetic signal
    rec = SyntheticSignalGenerator.generate("QPSK", sample_rate=1e6, symbol_rate=100e3, num_symbols=500)
    window.load_signal_record(rec)

    assert window.state_machine.current_state == AppState.READY
    assert window.current_signal is not None
    assert window.dock_workspace.signals_group.rowCount() == 1
    assert "Active Signal" in window.dock_workspace.signals_group.child(0).text() or "Synthetic Buffer" in window.lbl_file_status.text()

    window.close()
