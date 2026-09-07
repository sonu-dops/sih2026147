"""UI and pipeline state machine representation."""

from enum import Enum
from typing import Callable, List, Optional


class AppState(str, Enum):
    """Explicit states of the application and analysis engine."""
    EMPTY = "EMPTY"                   # No file loaded
    FILE_LOADING = "FILE_LOADING"     # File ingestion and validation in progress
    READY = "READY"                   # File loaded, parameters ready, awaiting analysis
    PROCESSING = "PROCESSING"         # Pipeline execution in progress
    PAUSED = "PAUSED"                 # Execution suspended
    COMPLETED = "COMPLETED"           # Analysis finished successfully
    ERROR = "ERROR"                   # Fatal or unhandled error occurred
    CANCELLED = "CANCELLED"           # User aborted the pipeline


class StateMachine:
    """State transition controller for the desktop application."""

    def __init__(self, initial_state: AppState = AppState.EMPTY):
        self._current_state = initial_state
        self._listeners: List[Callable[[AppState, AppState], None]] = []

    @property
    def current_state(self) -> AppState:
        return self._current_state

    def add_transition_listener(self, listener: Callable[[AppState, AppState], None]) -> None:
        """Register a callback when state changes: callback(old_state, new_state)."""
        self._listeners.append(listener)

    def transition_to(self, new_state: AppState) -> None:
        """Perform a state transition if valid and notify all registered listeners."""
        old_state = self._current_state
        if old_state == new_state:
            return

        # Validate legal state transitions
        valid = self._validate_transition(old_state, new_state)
        if not valid:
            raise ValueError(f"Illegal state transition from {old_state.value} to {new_state.value}")

        self._current_state = new_state
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception:
                pass

    def _validate_transition(self, from_state: AppState, to_state: AppState) -> bool:
        # Errors or Cancellation can happen from any state
        if to_state in (AppState.ERROR, AppState.CANCELLED):
            return True

        if from_state == AppState.EMPTY:
            return to_state in (AppState.FILE_LOADING, AppState.READY)
        elif from_state == AppState.FILE_LOADING:
            return to_state in (AppState.READY, AppState.EMPTY)
        elif from_state == AppState.READY:
            return to_state in (AppState.PROCESSING, AppState.FILE_LOADING, AppState.EMPTY)
        elif from_state == AppState.PROCESSING:
            return to_state in (AppState.PAUSED, AppState.COMPLETED)
        elif from_state == AppState.PAUSED:
            return to_state in (AppState.PROCESSING, AppState.READY)
        elif from_state in (AppState.COMPLETED, AppState.CANCELLED, AppState.ERROR):
            return to_state in (AppState.READY, AppState.PROCESSING, AppState.FILE_LOADING, AppState.EMPTY)

        return False
