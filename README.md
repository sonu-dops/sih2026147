# SIGNALINSIGHT

**Automated IQ/WAV Signal Analysis, Parameter Extraction & Modulation Classification**

SignalInsight is a production-grade, professional desktop engineering instrument for laboratory signal analyzers, SDR post-processing, and RF engineering workflows.

---

## Key Features

- **Multi-Format Ingestion**: Ingests raw `.IQ` binary recordings (with support for `int8`, `uint8`, `int16`, `uint16`, `int32`, `float32`, `float64`, `IQ`/`QI` interleaving, little/big endian), standard and RF floating-point `.WAV`, and **SigMF** metadata archives.
- **Scientific Provenance**: Complete traceability of all measurements. Parameters are explicitly tagged with their source (`[SIGMF]`, `[USER]`, `[ESTIMATED]`, `[CALCULATED]`, or `[CALIBRATION_REQUIRED]`) and numerical confidence levels.
- **High-Performance Memory Mapping**: Employs `numpy.memmap` and chunked streaming to handle multi-gigabyte recordings smoothly without blocking the UI or overflowing system RAM.
- **Rigorous DSP Engine**:
  - DC offset removal (mean and complex).
  - Normalization (RMS, Peak, or Uncalibrated absolute).
  - Analytic signal construction via Hilbert transform with boundary effect mitigation.
  - Numerically stable instantaneous amplitude, phase unwrapping, carrier detrending, and Savitzky-Golay smoothed instantaneous frequency.
  - Windowed FFT (Rectangular, Hann, Hamming, Blackman, Flat-top) and Welch PSD (dB/Hz).
  - Short-Time Fourier Transform (STFT) 2D Spectrogram.
- **Parameter Estimation**:
  - Baseband & RF Carrier frequency estimation with spectral peak interpolation.
  - Occupied Bandwidth (OBW at 90%, 95%, 99%) and -3dB / -6dB power thresholds.
  - Percentile and median noise floor estimation; in-band integrated SNR.
  - Multi-method Symbol Rate estimation (cyclostationary, transition timing, spectral autocorrelation).
- **Comprehensive Feature Extraction**:
  - Time-domain and envelope statistics (RMS, Crest factor, Skewness, Kurtosis, Zero-crossings).
  - Higher-Order Cumulants: $C_{20}, C_{21}, C_{40}, C_{41}, C_{42}$ and normalized invariants $f_{40}, f_{41}, f_{42}$.
  - Spectral moments (centroid, spread, skewness, kurtosis, flatness).
  - IQ imbalance (amplitude and phase imbalance metrics).
- **Automatic Modulation Classification (AMC)**:
  - Gradient-Boosted (`XGBoost`) classifier trained on invariant statistical and cumulant features.
  - Target classes: BPSK, QPSK, 8PSK, 16-QAM, FSK.
  - Rejection thresholding: low-confidence classifications are reported as `UNCERTAIN`.
  - Synthetic signal and dataset generator with configurable SNR, carrier offset, and timing jitter.
- **Synchronization & Demodulation**:
  - Matched filtering (Root-Raised Cosine and Raised Cosine).
  - Carrier phase & frequency recovery (Costas loop).
  - Symbol timing recovery (Gardner timing error detector).
  - Modular demodulators (BPSK, QPSK, 8PSK, 16-QAM, FSK) with Gray mapping, constellation display, and RMS EVM metrics.
- **Extensible Decoding Architecture**:
  - Strict non-arbitrary decoding: requires explicit framing/FEC/CRC configuration or reports `"Decoding unavailable — coding configuration not specified."`
- **Professional Desktop UI**:
  - PyQt6 + PyQtGraph professional light engineering workstation theme.
  - Dockable panels: Workspace Explorer, Properties Inspector, Analysis Control, Results Summary, Markers Manager, Message Console, and Processing Queue.
  - Interactive plot cursors, peak/delta markers, and level-of-detail decimation for large recordings.
- **Export & Reporting**:
  - Multi-page professional engineering PDF reports via ReportLab.
  - JSON and CSV structured result exports.
  - SigMF metadata export (`.sigmf-meta`).
