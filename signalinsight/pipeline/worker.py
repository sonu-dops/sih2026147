"""Asynchronous background worker for executing DSP pipelines without blocking the UI thread."""

from typing import Callable, Optional
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from signalinsight.core.models import AnalysisResult, SignalRecord
from signalinsight.pipeline.runner import PipelineOptions, PipelineRunner


class PipelineWorkerSignals(QObject):
    """Qt signals for reporting progress and results to the GUI thread."""
    progress = pyqtSignal(int, str)  # percent, stage_message
    finished = pyqtSignal(object)    # AnalysisResult
    error = pyqtSignal(str, str)     # error_message, technical_details
    cancelled = pyqtSignal()


class AnalysisWorker(QThread):
    """Dedicated background QThread for running the signal analysis pipeline."""

    def __init__(
        self,
        signal_rec: SignalRecord,
        options: Optional[PipelineOptions] = None,
        runner: Optional[PipelineRunner] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.signal_rec = signal_rec
        self.options = options or PipelineOptions()
        self.runner = runner or PipelineRunner()
        self.signals = PipelineWorkerSignals()

    def run(self) -> None:
        try:
            result = self.runner.run(
                self.signal_rec,
                options=self.options,
                progress_callback=self._on_progress,
            )
            self.signals.finished.emit(result)
        except InterruptedError:
            self.signals.cancelled.emit()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.signals.error.emit(str(e), tb)

    def cancel(self) -> None:
        self.runner.cancel()

    def _on_progress(self, pct: int, msg: str) -> None:
        self.signals.progress.emit(pct, msg)
