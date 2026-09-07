# SIGNALINSIGHT Architecture Documentation

## 1. System Overview

SignalInsight is structured as a modular monolithic desktop application with clean domain separation across:
- **`signalinsight.core`**: Fundamental models (`SignalRecord`, `ParameterValue`, `AnalysisResult`), provenance tracking (`ProvenanceSource`), exceptions, constants, and structured logging.
- **`signalinsight.io`**: High-performance loaders for WAV, raw binary IQ (with `numpy.memmap`), SigMF metadata parsing/export, file validation, and project persistence.
- **`signalinsight.dsp`**: Core digital signal processing algorithms (DC offset correction, RMS/peak normalization, FIR/IIR/RRC filtering, Hilbert transform, windowed FFT, Welch PSD, STFT Spectrogram).
- **`signalinsight.estimation`**: Statistical estimators for carrier frequency offset, occupied bandwidth (OBW 90%, 95%, 99%), noise floor, SNR, and symbol rate.
- **`signalinsight.features`**: Physics-based invariant feature extractors including 4th-order cumulants ($C_{20}, C_{21}, C_{40}, C_{41}, C_{42}$), spectral moments, and envelope statistics.
- **`signalinsight.amc`**: Automatic Modulation Classification using Gradient-Boosted Decision Trees (`XGBoost`), probability calibration, rejection thresholding (`UNCERTAIN`), and synthetic signal generators.
- **`signalinsight.synchronization`**: 2nd-order Costas loop carrier recovery, Gardner symbol timing recovery, and RRC matched filtering.
- **`signalinsight.demodulation`**: Constellation analysis, EVM calculation, and Gray-coded demodulators (BPSK, QPSK, 8PSK, 16-QAM, FSK).
- **`signalinsight.decoding`**: Optional framing/FEC framework with strict unconfigured reporting.
- **`signalinsight.pipeline`**: Orchestration engine with progress callbacks, cancellation checks, and background QThread workers.
- **`signalinsight.reporting`**: Export facilities for JSON, CSV, SigMF metadata, and ReportLab PDF reports.
- **`signalinsight.ui`**: PyQt6 + PyQtGraph dark workstation GUI with dockable widgets, interactive crosshair cursors, and state machine coordination.

---

## 2. Provenance Guarantee

Every metric displayed in the UI and reports carries an explicit `ProvenanceSource`:
- `[SIGMF]`: Read directly from standard SigMF metadata.
- `[USER]`: Explicitly supplied by the analyst in configuration dialogs.
- `[ESTIMATED]`: Inferred through mathematical estimators.
- `[CALCULATED]`: Deterministic closed-form mathematical calculation from sampled data.
- `[MEASURED]`: Calibrated measurement against known hardware standards.
- `[CALIBRATION_REQUIRED]`: Explicitly flags that physical conversion (e.g. dBm) requires known reference impedance and frontend gain.
