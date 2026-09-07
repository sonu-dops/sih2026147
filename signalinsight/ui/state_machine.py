"""UI action coordinator linked to the application state machine."""

from typing import Dict, Optional
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QPushButton

from signalinsight.core.state import AppState, StateMachine


class UIStateCoordinator:
    """Synchronizes toolbar actions and buttons with the application state machine."""

    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self._actions: Dict[str, QAction] = {}
        self._buttons: Dict[str, QPushButton] = {}
        self.state_machine.add_transition_listener(self._on_state_change)

    def register_action(self, name: str, action: QAction) -> None:
        self._actions[name] = action

    def register_button(self, name: str, button: QPushButton) -> None:
        self._buttons[name] = button

    def update_ui_for_state(self, state: AppState) -> None:
        """Configures enabled/disabled status of controls based on current state."""
        is_empty = state == AppState.EMPTY
        is_ready = state == AppState.READY
        is_processing = state == AppState.PROCESSING
        is_paused = state == AppState.PAUSED
        is_completed = state == AppState.COMPLETED

        # Run action / button
        can_run = is_ready or is_completed or is_paused
        if "run" in self._actions:
            self._actions["run"].setEnabled(can_run)
        if "run" in self._buttons:
            self._buttons["run"].setEnabled(can_run)

        # Stop action / button
        can_stop = is_processing or is_paused
        if "stop" in self._actions:
            self._actions["stop"].setEnabled(can_stop)
        if "stop" in self._buttons:
            self._buttons["stop"].setEnabled(can_stop)

        # Pause action / button
        if "pause" in self._actions:
            self._actions["pause"].setEnabled(is_processing)
        if "pause" in self._buttons:
            self._buttons["pause"].setEnabled(is_processing)

        # Export actions
        can_export = is_ready or is_completed
        for exp_key in ("export_data", "export_report", "export_sigmf"):
            if exp_key in self._actions:
                self._actions[exp_key].setEnabled(can_export)

    def _on_state_change(self, old_state: AppState, new_state: AppState) -> None:
        self.update_ui_for_state(new_state)
