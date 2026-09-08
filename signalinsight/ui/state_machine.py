"""UI action coordinator linked to the application state machine."""

from typing import Dict, List
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QPushButton

from signalinsight.core.state import AppState, StateMachine


class UIStateCoordinator:
    """Synchronizes toolbar actions and buttons with the application state machine."""

    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self._actions: Dict[str, List[QAction]] = {}
        self._buttons: Dict[str, List[QPushButton]] = {}
        self.state_machine.add_transition_listener(self._on_state_change)

    def register_action(self, name: str, action: QAction) -> None:
        if name not in self._actions:
            self._actions[name] = []
        if action not in self._actions[name]:
            self._actions[name].append(action)

    def register_button(self, name: str, button: QPushButton) -> None:
        if name not in self._buttons:
            self._buttons[name] = []
        if button not in self._buttons[name]:
            self._buttons[name].append(button)

    def update_ui_for_state(self, state: AppState) -> None:
        """Configures enabled/disabled status of controls based on current state."""
        is_ready = state == AppState.READY
        is_processing = state == AppState.PROCESSING
        is_paused = state == AppState.PAUSED
        is_completed = state == AppState.COMPLETED
        is_error = state == AppState.ERROR
        is_cancelled = state == AppState.CANCELLED

        # Run action / button - only allow running when idle
        can_run = (is_ready or is_completed or is_paused or is_error or is_cancelled) and not is_processing
        for act in self._actions.get("run", []):
            act.setEnabled(can_run)
        for btn in self._buttons.get("run", []):
            btn.setEnabled(can_run)

        # Stop action / button
        can_stop = is_processing or is_paused
        for act in self._actions.get("stop", []):
            act.setEnabled(can_stop)
        for btn in self._buttons.get("stop", []):
            btn.setEnabled(can_stop)

        # Pause action / button
        for act in self._actions.get("pause", []):
            act.setEnabled(is_processing)
        for btn in self._buttons.get("pause", []):
            btn.setEnabled(is_processing)

        # Export actions
        can_export = is_ready or is_completed
        for exp_key in ("export_data", "export_report", "export_sigmf"):
            for act in self._actions.get(exp_key, []):
                act.setEnabled(can_export)

    def _on_state_change(self, old_state: AppState, new_state: AppState) -> None:
        self.update_ui_for_state(new_state)
