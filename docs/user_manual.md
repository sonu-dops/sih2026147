# SIGNALINSIGHT User Manual & Operational Guide

## 1. Quick Start Guide

### Launching the Application
```bash
# Launch interactive desktop GUI
python -m signalinsight.main

# Or run headless analysis and generate a PDF report directly
python -m signalinsight.main --file path/to/signal.wav --report analysis_report.pdf
```

---

## 2. Ingesting Signals
1. **Drag and Drop**: Drag any `.iq`, `.wav`, or `.sigmf-meta` file into the main application window.
2. **File Menu**: Select `File -> Open Signal File...` (Ctrl+O).
3. **Synthetic Generator**: Select `File -> Generate Synthetic Signal...` (Ctrl+G) or click the **Generator** button in the toolbar to create test signals with known impairments.
4. **Raw IQ Import Configuration**:
   - When opening raw binary files without headers, the **File Import Configuration** dialog appears.
   - Specify Data Type (`int8`, `uint8`, `int16`, `int32`, `float32`, `float64`), IQ format (`IQ` or `QI`), Endianness (`Little Endian` / `Big Endian`), Sample Rate, and Center Frequency.
   - Click **Preview Slice** to inspect the waveform in real time before importing.

---

## 3. Keyboard Shortcuts
| Shortcut | Action |
|:---|:---|
| `Ctrl+O` | Open Signal File |
| `Ctrl+G` | Generate Synthetic Signal |
| `Ctrl+S` | Save Project Session |
| `Ctrl+E` | Export Engineering PDF Report |
| `F5` | Start Analysis Pipeline |
| `Esc` | Stop / Abort Current Analysis |
| `Alt+F4` | Exit SignalInsight |

---

## 4. Analysis Workspace Tabs
- **Time Domain**: Interactive I, Q, Magnitude, and Instantaneous Frequency plots with crosshair cursors and level-of-detail decimation.
- **Spectrum / PSD**: Centered windowed FFT and Welch PSD in dBFS/Hz with peak interpolation markers.
- **Spectrogram**: 2D STFT waterfall display with dynamic range slider and colormap selection (Viridis, Inferno, Turbo, Plasma).
- **Constellation**: Complex I/Q scatter plot, ideal reference points, decision crosshairs, and RMS/Peak EVM readouts.
- **Dual Comparison**: Side-by-side inspection and metrics delta table for comparing two recordings.

---

## 5. Exporting Results
- **PDF Technical Report**: `File -> Export -> Export Engineering PDF Report...` generates a formal vector document complete with tables, metrics, and provenance metadata.
- **JSON**: `File -> Export -> Export Analysis JSON...` exports the full machine-readable schema.
- **CSV**: `File -> Export -> Export Parameters CSV...` exports a flat table of all physical measurements.
- **SigMF**: `File -> Export -> Export SigMF Metadata...` writes standard `.sigmf-meta` with modulation annotations.
