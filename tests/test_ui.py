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

    # Test lazy tab rendering
    assert 0 not in window._dirty_tabs  # Active tab (0: Overview Dashboard) was rendered
    assert 1 in window._dirty_tabs      # Other tabs dirty until accessed
    assert 2 in window._dirty_tabs
    assert 3 in window._dirty_tabs
    assert 4 in window._dirty_tabs
    assert 5 in window._dirty_tabs

    # Verify Overview view was rendered
    assert window.overview_view.curve_spectrum.getData()[0] is not None

    # Switch to Spectrum tab (tab 2)
    window.analysis_tabs.setCurrentIndex(2)
    assert 2 not in window._dirty_tabs
    assert window.spectrum_view.curve_spec.getData()[0] is not None

    # Switch to Spectrogram tab (tab 3)
    window.analysis_tabs.setCurrentIndex(3)
    assert 3 not in window._dirty_tabs
    assert window.spectrogram_view._raw_spec_db is not None

    # Change dynamic range slider: should update image via cached STFT without recalculation
    window.spectrogram_view.slider_dr.setValue(50)
    assert window.spectrogram_view.img_item.image is not None

    # Switch to Demod & Bits tab (tab 5)
    window.analysis_tabs.setCurrentIndex(5)
    assert 5 not in window._dirty_tabs

    window.close()
