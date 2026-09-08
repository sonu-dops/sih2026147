"""Main application window for the SignalInsight workstation."""

import os
from pathlib import Path
import sys
from typing import Optional
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QDragEnterEvent, QDropEvent, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    COLOR_ERROR,
    COLOR_PRIMARY_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
)
from signalinsight.core.logging import logger
from signalinsight.core.models import AnalysisResult, SignalRecord
from signalinsight.core.state import AppState, StateMachine
from signalinsight.io.iq_loader import RawIQSignalLoader
from signalinsight.io.project import ProjectFile, ProjectManager
from signalinsight.io.sigmf_loader import SigMFSignalLoader
from signalinsight.io.wav_loader import WavSignalLoader
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner
from signalinsight.pipeline.worker import AnalysisWorker
from signalinsight.reporting.csv_export import CSVExporter
from signalinsight.reporting.json_export import JSONExporter
from signalinsight.reporting.pdf_report import PDFReportGenerator
from signalinsight.reporting.sigmf_export import SigMFExporter
from signalinsight.ui.dialogs.about_dialog import AboutDialog
from signalinsight.ui.dialogs.batch_dialog import BatchProcessorDialog
from signalinsight.ui.dialogs.generator_dialog import SignalGeneratorDialog

try:
    from backend.app.db.database import SessionLocal, init_db
    from backend.app.db.models.project import Project
    from backend.app.db.models.signal import SignalFile
    from backend.app.db.models.analysis import AnalysisRun, AnalysisResult as DBAnalysisResult, Feature
    from backend.app.db.models.amc import Classification
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
from signalinsight.ui.dialogs.import_dialog import FileImportDialog
from signalinsight.ui.dialogs.settings_dialog import SettingsDialog
from signalinsight.ui.docks.analysis_control import AnalysisControlDock
from signalinsight.ui.docks.markers_dock import MarkersDock
from signalinsight.ui.docks.message_console import MessageConsoleDock
from signalinsight.ui.docks.properties_dock import PropertiesDock
from signalinsight.ui.docks.queue_dock import QueueDock
from signalinsight.ui.docks.results_dock import ResultsSummaryDock
from signalinsight.ui.docks.workspace_tree import WorkspaceExplorerDock
from signalinsight.ui.state_machine import UIStateCoordinator
from signalinsight.ui.theme import get_workstation_stylesheet
from signalinsight.ui.views.comparison_view import ComparisonView
from signalinsight.ui.views.constellation_view import ConstellationView
from signalinsight.ui.views.spectrogram_view import SpectrogramView
from signalinsight.ui.views.spectrum_view import SpectrumView
from signalinsight.ui.views.time_view import TimeDomainView


class MainWindow(QMainWindow):
    """SignalInsight professional desktop engineering instrument main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE}")
        self.resize(1500, 950)
        self.setAcceptDrops(True)

        # State machine
        self.state_machine = StateMachine(AppState.EMPTY)
        self.state_coordinator = UIStateCoordinator(self.state_machine)

        # Signal and Analysis State
        self.current_signal: Optional[SignalRecord] = None
        self.current_result: Optional[AnalysisResult] = None
        self.worker: Optional[AnalysisWorker] = None
        self._dirty_tabs: set[int] = set()

        self._init_docks()
        self._init_central_views()
        self._init_menus()
        self._init_toolbar()
        self._init_statusbar()

        self.setStyleSheet(get_workstation_stylesheet())
        self.state_coordinator.update_ui_for_state(AppState.EMPTY)

        logger.info("System", f"{APP_NAME} v{APP_VERSION} initialized. Ready for signal ingestion.")

    def _init_central_views(self) -> None:
        self.central_stack = QStackedWidget()

        # 1. Initial Welcome Screen (when no file is loaded)
        self.welcome_screen = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_screen)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.setSpacing(14)

        lbl_logo = QLabel(APP_NAME)
        lbl_logo.setStyleSheet(f"font-size: 32pt; font-weight: bold; color: {COLOR_PRIMARY_ACCENT}; letter-spacing: 2px;")
        lbl_sub = QLabel(APP_SUBTITLE)
        lbl_sub.setStyleSheet("font-size: 11pt; color: #64748b; margin-bottom: 20px;")

        btn_row = QHBoxLayout()
        btn_open = QPushButton("Open Signal File (.IQ / .WAV)")
        btn_open.setObjectName("primary_action")
        btn_open.setMinimumHeight(40)
        btn_open.clicked.connect(self._open_signal_file)

        btn_gen = QPushButton("Generate Synthetic Signal")
        btn_gen.setMinimumHeight(40)
        btn_gen.clicked.connect(self._open_signal_generator)

        btn_row.addStretch()
        btn_row.addWidget(btn_open)
        btn_row.addWidget(btn_gen)
        btn_row.addStretch()

        sys_status = QLabel("DSP Engine: Ready | AMC Engine: Ready | Architecture: Modular 64-bit | SigMF: v1.0.0")
        sys_status.setStyleSheet("color: #64748b; font-family: monospace; font-size: 8.5pt; margin-top: 30px;")

        welcome_layout.addWidget(lbl_logo, alignment=Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(lbl_sub, alignment=Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addLayout(btn_row)
        welcome_layout.addWidget(sys_status, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_stack.addWidget(self.welcome_screen)

        # 2. Tabbed Analysis Workspace
        self.analysis_tabs = QTabWidget()
        self.time_view = TimeDomainView()
        self.spectrum_view = SpectrumView()
        self.spectrogram_view = SpectrogramView()
        self.constellation_view = ConstellationView()
        self.comparison_view = ComparisonView()

        self.analysis_tabs.addTab(self.time_view, "TIME DOMAIN")
        self.analysis_tabs.addTab(self.spectrum_view, "SPECTRUM / PSD")
        self.analysis_tabs.addTab(self.spectrogram_view, "SPECTROGRAM")
        self.analysis_tabs.addTab(self.constellation_view, "CONSTELLATION")
        self.analysis_tabs.addTab(self.comparison_view, "DUAL COMPARISON")
        self.analysis_tabs.currentChanged.connect(self._on_tab_changed)

        self.central_stack.addWidget(self.analysis_tabs)
        self.setCentralWidget(self.central_stack)

    def _init_docks(self) -> None:
        # Left Docks
        self.dock_workspace = WorkspaceExplorerDock(self)
        self.dock_properties = PropertiesDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_workspace)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_properties)

        self.dock_workspace.node_selected.connect(self._on_workspace_node_selected)

        # Right Docks
        self.dock_control = AnalysisControlDock(self)
        self.dock_results = ResultsSummaryDock(self)
        self.dock_markers = MarkersDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_control)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_results)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_markers)

        self.tabifyDockWidget(self.dock_results, self.dock_markers)
        self.dock_results.raise_()

        self.dock_control.run_requested.connect(self._start_analysis)
        self.dock_control.pause_requested.connect(self._pause_analysis)
        self.dock_control.stop_requested.connect(self._stop_analysis)
        self.dock_control.reset_requested.connect(self._reset_analysis)

        # Register Dock buttons with state coordinator
        self.state_coordinator.register_button("run", self.dock_control.btn_run)
        self.state_coordinator.register_button("stop", self.dock_control.btn_stop)
        self.state_coordinator.register_button("pause", self.dock_control.btn_pause)

        # Bottom Docks
        self.dock_console = MessageConsoleDock(self)
        self.dock_queue = QueueDock(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_queue)
        self.tabifyDockWidget(self.dock_console, self.dock_queue)
        self.dock_console.raise_()

    def _init_menus(self) -> None:
        menubar = self.menuBar()

        # FILE
        m_file = menubar.addMenu("&File")
        act_open_sig = QAction("&Open Signal File...", self)
        act_open_sig.setShortcut(QKeySequence("Ctrl+O"))
        act_open_sig.triggered.connect(self._open_signal_file)
        m_file.addAction(act_open_sig)

        act_gen_sig = QAction("&Generate Synthetic Signal...", self)
        act_gen_sig.setShortcut(QKeySequence("Ctrl+G"))
        act_gen_sig.triggered.connect(self._open_signal_generator)
        m_file.addAction(act_gen_sig)

        m_file.addSeparator()
        act_open_proj = QAction("Open Project...", self)
        act_save_proj = QAction("Save Project", self)
        act_save_proj.setShortcut(QKeySequence("Ctrl+S"))
        act_open_proj.triggered.connect(self._open_project)
        act_save_proj.triggered.connect(self._save_project)
        m_file.addAction(act_open_proj)
        m_file.addAction(act_save_proj)

        m_file.addSeparator()
        m_export = m_file.addMenu("Export")
        self.act_exp_json = QAction("Export Analysis JSON...", self)
        self.act_exp_json.triggered.connect(self._export_json)
        self.act_exp_csv = QAction("Export Parameters CSV...", self)
        self.act_exp_csv.triggered.connect(self._export_csv)
        self.act_exp_sigmf = QAction("Export SigMF Metadata...", self)
        self.act_exp_sigmf.triggered.connect(self._export_sigmf)
        self.act_exp_pdf = QAction("Export Engineering PDF Report...", self)
        self.act_exp_pdf.setShortcut(QKeySequence("Ctrl+E"))
        self.act_exp_pdf.triggered.connect(self._export_pdf)

        m_export.addAction(self.act_exp_pdf)
        m_export.addAction(self.act_exp_json)
        m_export.addAction(self.act_exp_csv)
        m_export.addAction(self.act_exp_sigmf)

        m_file.addSeparator()
        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        m_file.addAction(act_exit)

        # EDIT
        m_edit = menubar.addMenu("&Edit")
        act_prefs = QAction("&Preferences...", self)
        act_prefs.triggered.connect(self._open_preferences)
        m_edit.addAction(act_prefs)

        # VIEW
        m_view = menubar.addMenu("&View")
        m_view.addAction(self.dock_workspace.toggleViewAction())
        m_view.addAction(self.dock_properties.toggleViewAction())
        m_view.addAction(self.dock_control.toggleViewAction())
        m_view.addAction(self.dock_results.toggleViewAction())
        m_view.addAction(self.dock_markers.toggleViewAction())
        m_view.addAction(self.dock_console.toggleViewAction())
        m_view.addAction(self.dock_queue.toggleViewAction())

        # ANALYSIS
        m_analysis = menubar.addMenu("&Analysis")
        self.act_run = QAction("&Run Analysis", self)
        self.act_run.setShortcut(QKeySequence("F5"))
        self.act_run.triggered.connect(lambda: self.dock_control._on_run_clicked())
        self.act_stop = QAction("&Stop", self)
        self.act_stop.setShortcut(QKeySequence("Esc"))
        self.act_stop.triggered.connect(self._stop_analysis)
        m_analysis.addAction(self.act_run)
        m_analysis.addAction(self.act_stop)

        # TOOLS
        m_tools = menubar.addMenu("&Tools")
        act_batch = QAction("&Batch Processor...", self)
        act_batch.triggered.connect(self._open_batch_processor)
        m_tools.addAction(act_batch)
        m_tools.addAction(act_gen_sig)

        # HELP
        m_help = menubar.addMenu("&Help")
        act_about = QAction("&About SignalInsight...", self)
        act_about.triggered.connect(self._open_about)
        m_help.addAction(act_about)

        # State registration
        self.state_coordinator.register_action("run", self.act_run)
        self.state_coordinator.register_action("stop", self.act_stop)
        self.state_coordinator.register_action("export_report", self.act_exp_pdf)
        self.state_coordinator.register_action("export_data", self.act_exp_json)

    def _init_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar", self)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        btn_open = tb.addAction("Open")
        btn_open.setToolTip("Open Signal File (.IQ / .WAV / .SigMF)")
        btn_open.triggered.connect(self._open_signal_file)

        btn_gen = tb.addAction("Generator")
        btn_gen.setToolTip("Open Synthetic Signal Generator")
        btn_gen.triggered.connect(self._open_signal_generator)

        tb.addSeparator()

        self.tb_btn_run = QPushButton("RUN")
        self.tb_btn_run.setObjectName("primary_action")
        self.tb_btn_run.setStyleSheet(
            f"background-color: {COLOR_PRIMARY_ACCENT}; color: #ffffff; border: 1px solid #0369a1; border-radius: 3px; font-weight: bold; padding: 4px 12px;"
        )
        self.tb_btn_run.clicked.connect(lambda: self.dock_control._on_run_clicked())
        tb.addWidget(self.tb_btn_run)

        self.tb_btn_stop = QPushButton("STOP")
        self.tb_btn_stop.setEnabled(False)
        self.tb_btn_stop.clicked.connect(self._stop_analysis)
        tb.addWidget(self.tb_btn_stop)

        tb.addSeparator()

        btn_report = tb.addAction("Report (PDF)")
        btn_report.triggered.connect(self._export_pdf)

        btn_json = tb.addAction("Export JSON")
        btn_json.triggered.connect(self._export_json)

        tb.addSeparator()

        btn_batch = tb.addAction("Batch")
        btn_batch.triggered.connect(self._open_batch_processor)

        self.state_coordinator.register_button("run", self.tb_btn_run)
        self.state_coordinator.register_button("stop", self.tb_btn_stop)

    def _init_statusbar(self) -> None:
        sb = QStatusBar(self)
        self.setStatusBar(sb)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")

        self.lbl_sr_status = QLabel("Sample Rate: --")
        self.lbl_fc_status = QLabel("Center Freq: --")
        self.lbl_file_status = QLabel("File: (None)")
        self.lbl_engine_status = QLabel("DSP: Ready | AMC: Ready")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.lbl_backend_status = QLabel("DB: Connected (SQLite)" if DB_AVAILABLE else "DB: Standalone")
        self.lbl_backend_status.setStyleSheet("color: #0284c7; font-weight: bold;")

        sb.addWidget(self.lbl_status)
        sb.addWidget(self.progress_bar)
        sb.addPermanentWidget(self.lbl_file_status)
        sb.addPermanentWidget(self.lbl_sr_status)
        sb.addPermanentWidget(self.lbl_fc_status)
        sb.addPermanentWidget(self.lbl_backend_status)
        sb.addPermanentWidget(self.lbl_engine_status)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self._load_file_path(path)
                break

    def _open_signal_file(self) -> None:
        fn, _ = QFileDialog.getOpenFileName(
            self,
            "Open Signal Recording",
            "",
            "All Supported (*.wav *.iq *.raw *.bin *.dat *.complex *.sigmf-meta);;WAV Files (*.wav);;Raw IQ (*.iq *.raw *.bin *.dat *.complex);;SigMF (*.sigmf-meta)",
        )
        if fn:
            self._load_file_path(Path(fn))

    def _load_file_path(self, filepath: Path) -> None:
        ext = filepath.suffix.lower()
        try:
            if ext == ".wav":
                loader = WavSignalLoader()
                rec = loader.load(filepath)
            elif ext == ".sigmf-meta" or ext == ".sigmf-data":
                loader = SigMFSignalLoader()
                rec = loader.load(filepath)
            else:
                # Raw binary IQ file: open import config dialog
                dlg = FileImportDialog(filepath, self)
                if dlg.exec() == FileImportDialog.DialogCode.Accepted and dlg.imported_record:
                    rec = dlg.imported_record
                else:
                    return

            self.load_signal_record(rec)
        except Exception as e:
            QMessageBox.critical(self, "Signal Ingestion Error", f"Unable to ingest signal file:\n{e}")
            logger.error("IO", f"Failed loading {filepath.name}: {e}")

    def _open_signal_generator(self) -> None:
        dlg = SignalGeneratorDialog(self)
        if dlg.exec() == SignalGeneratorDialog.DialogCode.Accepted and dlg.generated_record:
            self.load_signal_record(dlg.generated_record)

    def load_signal_record(self, signal_rec: SignalRecord) -> None:
        self.current_signal = signal_rec
        self.current_result = None

        # Mark all tabs dirty and only render the currently visible tab
        self._dirty_tabs = {0, 1, 2, 3, 4}
        self.central_stack.setCurrentWidget(self.analysis_tabs)
        current_idx = self.analysis_tabs.currentIndex()
        self._render_tab(current_idx)
        self._dirty_tabs.discard(current_idx)

        # Update Docks
        self.dock_workspace.set_active_signal(signal_rec)
        self.dock_properties.set_signal(signal_rec)

        # Update Status Bar
        fn_str = signal_rec.source_file.name if signal_rec.source_file else "Synthetic Buffer"
        self.lbl_file_status.setText(f"File: {fn_str}")
        sr_val = signal_rec.sample_rate
        sr_str = f"{sr_val/1e6:.3f} Msps" if sr_val >= 1e6 else f"{sr_val/1e3:.1f} ksps"
        self.lbl_sr_status.setText(f"Sample Rate: {sr_str}")
        fc_val = signal_rec.center_frequency
        fc_str = f"{fc_val/1e6:.3f} MHz" if fc_val >= 1e6 else f"{fc_val:,.0f} Hz"
        self.lbl_fc_status.setText(f"Center: {fc_str}")

        self.state_machine.transition_to(AppState.READY)
        logger.info("Workspace", f"Signal loaded: {fn_str} ({signal_rec.sample_count:,} samples, {signal_rec.duration:.4f} s)")

    def _on_tab_changed(self, index: int) -> None:
        """Lazily renders a tab only when the user switches to it if marked dirty."""
        if index in self._dirty_tabs:
            self._render_tab(index)
            self._dirty_tabs.discard(index)

    def _render_tab(self, index: int) -> None:
        """Renders specific analysis tab data on demand."""
        if self.current_signal is None:
            return
        if index == 0:
            self.time_view.set_signal(self.current_signal)
        elif index == 1:
            self.spectrum_view.set_signal(self.current_signal)
        elif index == 2:
            self.spectrogram_view.set_signal(self.current_signal)
        elif index == 3:
            if self.current_result and self.current_result.demodulation_result:
                self.constellation_view.set_demod_result(self.current_result.demodulation_result)
            else:
                self.constellation_view.set_raw_symbols(self.current_signal.samples)
        elif index == 4:
            # Dual comparison tab
            pass

    def _start_analysis(self, options: PipelineOptions) -> None:
        if self.current_signal is None:
            QMessageBox.warning(self, "No Signal", "Please load or generate an RF signal before running analysis.")
            return

        # Prevent duplicate concurrent analysis executions and clean up previous worker
        if self.worker is not None:
            if self.worker.isRunning():
                logger.warning("Pipeline", "Analysis is already executing. Ignoring duplicate run request.")
                return
            try:
                self.worker.wait(1000)
            except Exception:
                pass
            self.worker = None

        self.state_machine.transition_to(AppState.PROCESSING)
        self.lbl_status.setText("Processing...")
        self.lbl_status.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Launch QThread background worker with parent lifecycle
        self.worker = AnalysisWorker(self.current_signal, options=options, parent=self)
        self.worker.signals.progress.connect(self._on_analysis_progress)
        self.worker.signals.finished.connect(self._on_analysis_finished)
        self.worker.signals.error.connect(self._on_analysis_error)
        self.worker.signals.cancelled.connect(self._on_analysis_cancelled)
        self.worker.finished.connect(self._on_worker_thread_done)
        self.worker.start()

    def _on_worker_thread_done(self) -> None:
        """Invoked when the background QThread terminates cleanly."""
        pass

    def _pause_analysis(self) -> None:
        # Toggle pause state
        if self.state_machine.current_state == AppState.PROCESSING:
            self.state_machine.transition_to(AppState.PAUSED)
            self.lbl_status.setText("Paused")
            self.lbl_status.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold;")

    def _stop_analysis(self) -> None:
        if self.worker:
            self.worker.cancel()
        self.state_machine.transition_to(AppState.CANCELLED)
        self.lbl_status.setText("Cancelled")
        self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")
        self.progress_bar.setVisible(False)

    def _reset_analysis(self) -> None:
        if self.current_signal:
            self.load_signal_record(self.current_signal)

    def _on_analysis_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"Processing ({pct}%): {msg}")

    def _on_analysis_finished(self, result: AnalysisResult) -> None:
        self.current_result = result
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Completed")
        self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")
        self.state_machine.transition_to(AppState.COMPLETED)

        try:
            # Update Results Summary Dock
            self.dock_results.set_result(result)
        except Exception as e:
            logger.error("UI", f"Error updating results dock: {e}")

        try:
            # Update Constellation View if demodulation result exists
            if result.demodulation_result:
                if self.analysis_tabs.currentIndex() == 3:
                    self.constellation_view.set_demod_result(result.demodulation_result)
                    self._dirty_tabs.discard(3)
                else:
                    self._dirty_tabs.add(3)
        except Exception as e:
            logger.error("UI", f"Error updating constellation view: {e}")

        try:
            # Persist results to database
            self._persist_analysis_to_db(result)
        except Exception as e:
            logger.error("Database", f"Error persisting analysis to database: {e}")

        logger.info(
            "Pipeline",
            f"Analysis finished successfully in {result.processing_times_ms.get('total_pipeline_ms', 0.0):.1f} ms",
        )

    def _on_analysis_error(self, err_msg: str, details: str) -> None:
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Error")
        self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")
        self.state_machine.transition_to(AppState.ERROR)
        QMessageBox.critical(self, "Analysis Pipeline Error", f"{err_msg}\n\nDetails:\n{details[:500]}")
        logger.error("Pipeline", f"Pipeline error: {err_msg}", details=details)

    def _on_analysis_cancelled(self) -> None:
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Cancelled")
        self.state_machine.transition_to(AppState.CANCELLED)

    def _on_workspace_node_selected(self, node_tag: str) -> None:
        tag = node_tag.lower()
        if "time" in tag:
            self.analysis_tabs.setCurrentWidget(self.time_view)
        elif "spectrum" in tag or "freq" in tag:
            self.analysis_tabs.setCurrentWidget(self.spectrum_view)
        elif "spectrogram" in tag:
            self.analysis_tabs.setCurrentWidget(self.spectrogram_view)
        elif "constellation" in tag:
            self.analysis_tabs.setCurrentWidget(self.constellation_view)
        elif "active_signal" in tag:
            self.analysis_tabs.setCurrentWidget(self.time_view)

    def _export_json(self) -> None:
        if not self.current_result:
            QMessageBox.information(self, "No Results", "Please run analysis before exporting.")
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export JSON Results", "analysis_results.json", "JSON (*.json)")
        if fn:
            JSONExporter.export(self.current_result, Path(fn))
            QMessageBox.information(self, "Export Complete", f"Saved JSON results to:\n{fn}")

    def _export_csv(self) -> None:
        if not self.current_result:
            QMessageBox.information(self, "No Results", "Please run analysis before exporting.")
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export Parameters CSV", "signal_parameters.csv", "CSV (*.csv)")
        if fn:
            CSVExporter.export(self.current_result, Path(fn))
            QMessageBox.information(self, "Export Complete", f"Saved CSV parameters to:\n{fn}")

    def _export_sigmf(self) -> None:
        if not self.current_signal:
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export SigMF Metadata", "capture.sigmf-meta", "SigMF (*.sigmf-meta)")
        if fn:
            SigMFExporter.export_metadata(self.current_signal, Path(fn), analysis_result=self.current_result)
            QMessageBox.information(self, "Export Complete", f"Saved SigMF metadata to:\n{fn}")

    def _export_pdf(self) -> None:
        if not self.current_result:
            QMessageBox.information(self, "No Results", "Please run analysis before exporting a technical report.")
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export Engineering PDF Report", "technical_report.pdf", "PDF (*.pdf)")
        if fn:
            PDFReportGenerator.generate(self.current_result, Path(fn))
            QMessageBox.information(self, "Report Generated", f"Saved engineering PDF report to:\n{fn}")

    def _open_batch_processor(self) -> None:
        dlg = BatchProcessorDialog(self)
        dlg.exec()

    def _open_preferences(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()

    def _open_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    def _save_project(self) -> None:
        """Saves project to database and optionally to disk as .siproj."""
        fn, _ = QFileDialog.getSaveFileName(self, "Save SignalInsight Project", "project.siproj", "SignalInsight Project (*.siproj)")
        if not fn:
            return
        proj_name = Path(fn).stem
        if DB_AVAILABLE:
            try:
                with SessionLocal() as db:
                    p = db.query(Project).filter(Project.name == proj_name).first()
                    if not p:
                        p = Project(name=proj_name, description=f"Saved from workstation: {fn}")
                        db.add(p)
                        db.commit()
            except Exception as e:
                logger.warning("Project", f"DB project save fallback: {e}")

        # Also serialize JSON project file
        proj = ProjectFile()
        proj.metadata.name = proj_name
        if self.current_signal and self.current_signal.source_file:
            proj.signal_files = [str(self.current_signal.source_file)]
            proj.active_signal_file = str(self.current_signal.source_file)
        ProjectManager.save_project(proj, Path(fn))
        QMessageBox.information(self, "Project Saved", f"Project saved successfully:\n{fn}")

    def _open_project(self) -> None:
        """Loads project from file or database."""
        fn, _ = QFileDialog.getOpenFileName(self, "Open SignalInsight Project", "", "SignalInsight Project (*.siproj)")
        if not fn:
            return
        try:
            proj = ProjectManager.load_project(Path(fn))
            if proj.active_signal_file and Path(proj.active_signal_file).exists():
                self._load_file_path(Path(proj.active_signal_file))
            QMessageBox.information(self, "Project Loaded", f"Loaded project: {proj.metadata.name}")
        except Exception as e:
            QMessageBox.critical(self, "Project Error", f"Unable to open project:\n{e}")

    def _persist_analysis_to_db(self, result: AnalysisResult) -> None:
        """Persists the completed analysis run and metrics to the database."""
        if not DB_AVAILABLE or not self.current_signal:
            return
        try:
            with SessionLocal() as db:
                src_path = str(self.current_signal.source_file) if self.current_signal.source_file else "Synthetic"
                sig = db.query(SignalFile).filter(SignalFile.file_hash == result.file_hash_sha256).first()
                if not sig:
                    sig = SignalFile(
                        filename=Path(src_path).name,
                        original_path=src_path,
                        file_hash=result.file_hash_sha256 or "hash_in_memory",
                        file_size=self.current_signal.sample_count * 8,
                        format="WAV" if src_path.endswith(".wav") else "IQ",
                        data_type=self.current_signal.data_type,
                        sample_count=self.current_signal.sample_count,
                        sample_rate=self.current_signal.sample_rate,
                        center_frequency=self.current_signal.center_frequency,
                        duration=self.current_signal.duration,
                    )
                    db.add(sig)
                    db.commit()
                    db.refresh(sig)

                run = AnalysisRun(
                    signal_file_id=sig.id,
                    status="COMPLETED",
                    started_at=result.timestamp,
                    completed_at=result.timestamp,
                    pipeline_version="1.0.0",
                )
                db.add(run)
                db.commit()
                db.refresh(run)

                db_res = DBAnalysisResult(
                    analysis_run_id=run.id,
                    carrier_frequency=result.carrier_frequency.value,
                    carrier_offset=result.carrier_offset.value,
                    symbol_rate=result.symbol_rate.value,
                    occupied_bandwidth=result.occupied_bw_99.value,
                    bandwidth_3db=result.bandwidth_3db.value,
                    snr=result.snr_db.value,
                    signal_power=result.signal_power.value,
                    noise_floor=result.noise_floor.value,
                    dc_offset_i=result.dc_offset_i.value,
                    dc_offset_q=result.dc_offset_q.value,
                    confidence=1.0,
                    quality="HIGH",
                )
                db.add(db_res)

                if result.modulation_result:
                    clf = Classification(
                        analysis_run_id=run.id,
                        predicted_class=result.modulation_result.predicted_modulation,
                        confidence=result.modulation_result.confidence,
                        class_probabilities=result.modulation_result.class_probabilities,
                        model_version=result.modulation_result.model_version,
                    )
                    db.add(clf)

                db.commit()
                logger.info("Database", f"Persisted analysis run {run.id} for signal {sig.filename}")
        except Exception as e:
            logger.warning("Database", f"Failed auto-persisting analysis run to database: {e}")

    def closeEvent(self, event) -> None:
        """Ensures background threads are safely terminated before exiting."""
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
        event.accept()
