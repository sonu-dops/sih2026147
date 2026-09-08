"""Physical, mathematical, and DSP constants for SignalInsight."""

import numpy as np

# Application Metadata
APP_NAME = "SIGNALINSIGHT"
APP_SUBTITLE = "Automated IQ/WAV Signal Analysis, Parameter Extraction & Modulation Classification"
APP_VERSION = "1.0.0"

# Numerical Limits & Tolerances
EPSILON = 1e-15
MIN_SIGNAL_LENGTH = 32
DEFAULT_FFT_SIZE = 2048
MAX_FFT_SIZE = 65536
MIN_FFT_SIZE = 128

# Standard Supported Windows
WINDOW_RECTANGULAR = "Rectangular"
WINDOW_HANN = "Hann"
WINDOW_HAMMING = "Hamming"
WINDOW_BLACKMAN = "Blackman"
WINDOW_FLATTOP = "Flat-top"

SUPPORTED_WINDOWS = [
    WINDOW_HANN,
    WINDOW_HAMMING,
    WINDOW_BLACKMAN,
    WINDOW_FLATTOP,
    WINDOW_RECTANGULAR,
]

# Supported Modulation Classes for AMC
MOD_BPSK = "BPSK"
MOD_QPSK = "QPSK"
MOD_8PSK = "8PSK"
MOD_16QAM = "16-QAM"
MOD_FSK = "FSK"
MOD_UNCERTAIN = "UNCERTAIN"

SUPPORTED_MODULATIONS = [
    MOD_BPSK,
    MOD_QPSK,
    MOD_8PSK,
    MOD_16QAM,
    MOD_FSK,
]

# Confidence & Threshold Defaults
DEFAULT_CONFIDENCE_THRESHOLD = 0.50
HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.50

# Bandwidth Occupancy Percentages
OBW_PERCENTAGES = [0.90, 0.95, 0.99]

# Color Palette (Light Professional Engineering Workstation Theme)
COLOR_BG_DARK = "#f1f5f9"           # Light slate / clean laboratory background
COLOR_BG_PANEL = "#ffffff"          # Crisp white panels
COLOR_BORDER = "#cbd5e1"            # Subtle light border
COLOR_PRIMARY_ACCENT = "#0284c7"    # Professional Instrument Cyan/Blue
COLOR_SECONDARY_ACCENT = "#0369a1"  # Deep Blue
COLOR_SUCCESS = "#16a34a"           # Technical Green
COLOR_WARNING = "#d97706"           # Amber
COLOR_ERROR = "#dc2626"             # Signal Red
COLOR_TEXT_WHITE = "#0f172a"        # High-contrast dark slate text
COLOR_TEXT_MUTED = "#64748b"        # Muted slate secondary text
COLOR_PLOT_BG = "#ffffff"           # Clean white plot canvas
COLOR_GRID = "#e2e8f0"              # Light grid lines
COLOR_TRACE_I = "#0284c7"           # Blue/Cyan for I
COLOR_TRACE_Q = "#dc2626"           # Red for Q
COLOR_TRACE_MAG = "#16a34a"         # Emerald Green for Magnitude
COLOR_TRACE_PHASE = "#d97706"       # Amber for Phase
COLOR_TRACE_FREQ = "#7c3aed"        # Deep Violet for Frequency
COLOR_TRACE_PSD = "#0284c7"         # Cyan/Blue for PSD
COLOR_CONSTELLATION = "#0284c7"     # Blue for symbols
COLOR_CONSTELLATION_IDEAL = "#dc2626" # Red crosshairs for ideal

