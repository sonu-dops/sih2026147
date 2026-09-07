"""Synthetic Signal Generator dialog for creating test waveforms."""

from typing import Optional
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from signalinsight.amc.synthetic import SyntheticSignalGenerator
from signalinsight.core.constants import SUPPORTED_MODULATIONS
from signalinsight.core.models import SignalRecord


class SignalGeneratorDialog(QDialog):
    """Generates synthetic modulated waveforms with known ground truth."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.generated_record: Optional[SignalRecord] = None
        self.setWindowTitle("Synthetic Signal Generator")
        self.resize(450, 420)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        grp = QGroupBox("WAVEFORM & IMPAIRMENT PARAMETERS")
        form = QFormLayout(grp)

        self.combo_mod = QComboBox()
        self.combo_mod.addItems(SUPPORTED_MODULATIONS)
        form.addRow("Modulation Scheme:", self.combo_mod)

        self.spin_sr = QDoubleSpinBox()
        self.spin_sr.setRange(1e3, 100e6)
        self.spin_sr.setValue(1_000_000.0)
        self.spin_sr.setSuffix(" Hz")
        form.addRow("Sample Rate:", self.spin_sr)

        self.spin_sym_rate = QDoubleSpinBox()
        self.spin_sym_rate.setRange(1e2, 10e6)
        self.spin_sym_rate.setValue(100_000.0)
        self.spin_sym_rate.setSuffix(" Baud")
        form.addRow("Symbol Rate:", self.spin_sym_rate)

        self.spin_symbols = QSpinBox()
        self.spin_symbols.setRange(100, 100_000)
        self.spin_symbols.setValue(2000)
        form.addRow("Number of Symbols:", self.spin_symbols)

        self.spin_snr = QDoubleSpinBox()
        self.spin_snr.setRange(-20.0, 50.0)
        self.spin_snr.setValue(20.0)
        self.spin_snr.setSuffix(" dB")
        form.addRow("SNR (AWGN):", self.spin_snr)

        self.spin_cfo = QDoubleSpinBox()
        self.spin_cfo.setRange(-500_000.0, 500_000.0)
        self.spin_cfo.setValue(5000.0)
        self.spin_cfo.setSuffix(" Hz")
        form.addRow("Carrier Offset (CFO):", self.spin_cfo)

        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999)
        self.spin_seed.setValue(42)
        form.addRow("Random Seed:", self.spin_seed)

        layout.addWidget(grp)

        btn_row = QHBoxLayout()
        self.btn_gen = QPushButton("Generate & Load")
        self.btn_gen.setObjectName("primary_action")
        self.btn_gen.clicked.connect(self._do_generate)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_gen)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _do_generate(self) -> None:
        rec = SyntheticSignalGenerator.generate(
            modulation=self.combo_mod.currentText(),
            sample_rate=self.spin_sr.value(),
            symbol_rate=self.spin_sym_rate.value(),
            num_symbols=self.spin_symbols.value(),
            snr_db=self.spin_snr.value(),
            carrier_offset_hz=self.spin_cfo.value(),
            seed=self.spin_seed.value(),
        )
        self.generated_record = rec
        self.accept()
