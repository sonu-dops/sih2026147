"""Right Analysis Control dock panel."""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from signalinsight.core.constants import COLOR_PRIMARY_ACCENT, COLOR_SUCCESS, COLOR_WARNING, SUPPORTED_MODULATIONS
from signalinsight.pipeline.runner import PipelineOptions


class AnalysisControlDock(QDockWidget):
    """Analysis pipeline configuration and execution trigger controls."""

    run_requested = pyqtSignal(object)  # PipelineOptions
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("ANALYSIS CONTROL", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self._init_ui()

    def _init_ui(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Mode Selection
        grp_mode = QGroupBox("PIPELINE MODE")
        mode_layout = QVBoxLayout(grp_mode)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(
            [
                "Automatic (Full Pipeline)",
                "Parameter Estimation Only",
                "Modulation Classification Only",
                "Synchronization Only",
                "Demodulation Only",
                "Custom Pipeline",
            ]
        )
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.combo_mode)

        # Target Modulation Override
        lbl_target = QLabel("Target Modulation:")
        lbl_target.setStyleSheet("color: #64748b; font-size: 8.5pt;")
        self.combo_target_mod = QComboBox()
        self.combo_target_mod.addItem("Auto")
        self.combo_target_mod.addItems(SUPPORTED_MODULATIONS)
        mode_layout.addWidget(lbl_target)
        mode_layout.addWidget(self.combo_target_mod)
        layout.addWidget(grp_mode)

        # Stage Checkboxes
        grp_stages = QGroupBox("PIPELINE STAGES")
        stages_layout = QVBoxLayout(grp_stages)
        self.chk_dc = QCheckBox("Remove DC Offset")
        self.chk_dc.setChecked(True)
        self.chk_norm = QCheckBox("Normalize RMS")
        self.chk_norm.setChecked(False)
        self.chk_params = QCheckBox("Estimate Parameters")
        self.chk_params.setChecked(True)
        self.chk_features = QCheckBox("Extract Features")
        self.chk_features.setChecked(True)
        self.chk_amc = QCheckBox("Run Modulation Classifier (AMC)")
        self.chk_amc.setChecked(True)
        self.chk_sync = QCheckBox("Run Synchronization (Carrier/Timing)")
        self.chk_sync.setChecked(True)
        self.chk_demod = QCheckBox("Run Demodulation")
        self.chk_demod.setChecked(True)
        self.chk_decode = QCheckBox("Run Decoding (FEC/CRC)")
        self.chk_decode.setChecked(False)

        stages_layout.addWidget(self.chk_dc)
        stages_layout.addWidget(self.chk_norm)
        stages_layout.addWidget(self.chk_params)
        stages_layout.addWidget(self.chk_features)
        stages_layout.addWidget(self.chk_amc)
        stages_layout.addWidget(self.chk_sync)
        stages_layout.addWidget(self.chk_demod)
        stages_layout.addWidget(self.chk_decode)
        layout.addWidget(grp_stages)

        # Action Buttons
        grp_actions = QGroupBox("EXECUTION")
        act_layout = QVBoxLayout(grp_actions)
        self.btn_run = QPushButton("RUN ANALYSIS")
        self.btn_run.setObjectName("primary_action")
        self.btn_run.setStyleSheet(
            f"background-color: {COLOR_PRIMARY_ACCENT}; color: #ffffff; border: 1px solid #0369a1; border-radius: 3px; font-size: 10pt; font-weight: bold; padding: 8px;"
        )
        self.btn_run.clicked.connect(self._on_run_clicked)

        row_btns = QHBoxLayout()
        self.btn_pause = QPushButton("PAUSE")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.pause_requested.emit)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested.emit)

        self.btn_reset = QPushButton("RESET")
        self.btn_reset.clicked.connect(self.reset_requested.emit)

        row_btns.addWidget(self.btn_pause)
        row_btns.addWidget(self.btn_stop)
        row_btns.addWidget(self.btn_reset)

        act_layout.addWidget(self.btn_run)
        act_layout.addLayout(row_btns)
        layout.addWidget(grp_actions)

        # Advanced Settings
        grp_adv = QGroupBox("HARDWARE & CHUNKING")
        adv_layout = QVBoxLayout(grp_adv)
        lbl_workers = QLabel("CPU Workers:")
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 16)
        self.spin_workers.setValue(4)
        adv_layout.addWidget(lbl_workers)
        adv_layout.addWidget(self.spin_workers)
        layout.addWidget(grp_adv)

        layout.addStretch()
        self.setWidget(content)

    def _on_mode_changed(self, idx: int) -> None:
        text = self.combo_mode.currentText()
        if "Full Pipeline" in text:
            self.chk_dc.setChecked(True)
            self.chk_params.setChecked(True)
            self.chk_features.setChecked(True)
            self.chk_amc.setChecked(True)
            self.chk_sync.setChecked(True)
            self.chk_demod.setChecked(True)
            self.chk_decode.setChecked(False)
        elif "Parameter Estimation Only" in text:
            self.chk_params.setChecked(True)
            self.chk_features.setChecked(False)
            self.chk_amc.setChecked(False)
            self.chk_sync.setChecked(False)
            self.chk_demod.setChecked(False)
        elif "Modulation Classification Only" in text:
            self.chk_params.setChecked(False)
            self.chk_features.setChecked(True)
            self.chk_amc.setChecked(True)
            self.chk_sync.setChecked(False)
            self.chk_demod.setChecked(False)

    def _on_run_clicked(self) -> None:
        target = self.combo_target_mod.currentText()
        opts = PipelineOptions(
            remove_dc=self.chk_dc.isChecked(),
            normalize_rms=self.chk_norm.isChecked(),
            estimate_parameters=self.chk_params.isChecked(),
            extract_features=self.chk_features.isChecked(),
            run_amc=self.chk_amc.isChecked(),
            run_sync=self.chk_sync.isChecked(),
            run_demod=self.chk_demod.isChecked(),
            run_decode=self.chk_decode.isChecked(),
            target_modulation=target,
        )
        self.run_requested.emit(opts)
