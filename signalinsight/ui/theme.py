"""Professional Light Engineering Workstation theme for PyQt6."""

from signalinsight.core.constants import (
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_PRIMARY_ACCENT,
    COLOR_SECONDARY_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_TEXT_WHITE,
    COLOR_TEXT_MUTED,
    COLOR_PLOT_BG,
    COLOR_GRID,
)


def get_workstation_stylesheet(mode: str = "light") -> str:
    """Returns professional engineering workstation QSS stylesheet (light mode by default)."""
    if mode.lower() == "dark":
        bg_app = "#0a0e14"
        bg_panel = "#12171f"
        border = "#232a35"
        text_primary = "#f0f6fc"
        text_muted = "#8b949e"
        accent = "#00d2ff"
        accent_dark = "#0056b3"
        tree_bg = "#0d1219"
        header_bg = "#12171f"
        tab_bg = "#12171f"
        input_bg = "#0a0e14"
        btn_bg = "#1a2332"
        btn_hover = "#243144"
        status_bg = "#12171f"
        scroll_bg = "#0a0e14"
        scroll_handle = "#252d3a"
    else:
        # Default Light Mode
        bg_app = COLOR_BG_DARK        # #f1f5f9
        bg_panel = COLOR_BG_PANEL     # #ffffff
        border = COLOR_BORDER         # #cbd5e1
        text_primary = COLOR_TEXT_WHITE # #0f172a
        text_muted = COLOR_TEXT_MUTED # #64748b
        accent = COLOR_PRIMARY_ACCENT # #0284c7
        accent_dark = COLOR_SECONDARY_ACCENT # #0369a1
        tree_bg = "#ffffff"
        header_bg = "#f8fafc"
        tab_bg = "#f1f5f9"
        input_bg = "#ffffff"
        btn_bg = "#ffffff"
        btn_hover = "#f8fafc"
        status_bg = "#ffffff"
        scroll_bg = "#f1f5f9"
        scroll_handle = "#cbd5e1"

    return f"""
    /* Global Application Styles */
    QMainWindow, QDialog, QWidget {{
        background-color: {bg_app};
        color: {text_primary};
        font-family: "Segoe UI", "SF Pro Display", "Roboto", sans-serif;
        font-size: 9pt;
    }}

    /* Menu Bar */
    QMenuBar {{
        background-color: {bg_panel};
        color: {text_primary};
        border-bottom: 1px solid {border};
        padding: 2px 6px;
    }}
    QMenuBar::item {{
        background: transparent;
        padding: 4px 10px;
        border-radius: 2px;
    }}
    QMenuBar::item:selected {{
        background-color: #e2e8f0;
        color: {accent};
    }}
    QMenu {{
        background-color: {bg_panel};
        color: {text_primary};
        border: 1px solid {border};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 5px 24px 5px 12px;
        border-radius: 2px;
    }}
    QMenu::item:selected {{
        background-color: {accent};
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {border};
        margin: 4px 0px;
    }}

    /* Toolbar */
    QToolBar {{
        background-color: {bg_panel};
        border-bottom: 1px solid {border};
        spacing: 4px;
        padding: 3px 6px;
    }}
    QToolButton {{
        background-color: transparent;
        color: {text_primary};
        border: 1px solid transparent;
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 8.5pt;
        font-weight: 500;
    }}
    QToolButton:hover {{
        background-color: #e2e8f0;
        border: 1px solid {border};
        color: {accent};
    }}
    QToolButton:pressed {{
        background-color: #cbd5e1;
    }}
    QToolButton:disabled {{
        color: #94a3b8;
    }}

    /* Dock Widgets */
    QDockWidget {{
        color: {text_primary};
        font-size: 9pt;
        font-weight: 600;
        titlebar-close-icon: url();
        titlebar-normal-icon: url();
    }}
    QDockWidget::title {{
        background-color: #f8fafc;
        border-bottom: 1px solid {border};
        padding: 6px 10px;
        text-align: left;
        letter-spacing: 0.5px;
    }}

    /* Tree View / Workspace Explorer */
    QTreeView, QListView, QTableView {{
        background-color: {tree_bg};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 2px;
        selection-background-color: #e0f2fe;
        selection-color: {accent_dark};
        outline: none;
        alternate-background-color: #f8fafc;
    }}
    QHeaderView::section {{
        background-color: {header_bg};
        color: {text_muted};
        padding: 4px 8px;
        border: none;
        border-right: 1px solid {border};
        border-bottom: 1px solid {border};
        font-size: 8pt;
        font-weight: 600;
        text-transform: uppercase;
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {border};
        background-color: {bg_panel};
    }}
    QTabBar::tab {{
        background-color: {tab_bg};
        color: {text_muted};
        padding: 6px 16px;
        border: 1px solid {border};
        border-bottom: none;
        margin-right: 2px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background-color: {bg_panel};
        color: {accent};
        border-top: 2px solid {accent};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: #e2e8f0;
        color: {text_primary};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {btn_bg};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 3px;
        padding: 5px 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {btn_hover};
        border: 1px solid {accent};
        color: {accent};
    }}
    QPushButton:pressed {{
        background-color: #e2e8f0;
    }}
    QPushButton:disabled {{
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #94a3b8;
    }}
    QPushButton#primary_action {{
        background-color: {accent};
        border: 1px solid {accent_dark};
        color: #ffffff;
        font-weight: 600;
    }}
    QPushButton#primary_action:hover {{
        background-color: {accent_dark};
        border: 1px solid {accent_dark};
        color: #ffffff;
    }}

    /* Inputs, ComboBox, SpinBox */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {input_bg};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 2px;
        padding: 4px 8px;
        selection-background-color: #bae6fd;
        selection-color: {text_primary};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 18px;
    }}

    /* GroupBox */
    QGroupBox {{
        background-color: {bg_panel};
        border: 1px solid {border};
        border-radius: 3px;
        margin-top: 14px;
        padding-top: 10px;
        font-weight: 600;
        font-size: 8.5pt;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0px 5px;
        color: {accent};
    }}

    /* CheckBoxes & RadioButtons */
    QCheckBox, QRadioButton {{
        color: {text_primary};
        spacing: 6px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        background-color: {input_bg};
        border: 1px solid {border};
        border-radius: 2px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {accent};
        border: 1px solid {accent};
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        height: 4px;
        background: {border};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {accent};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: #ffffff;
        border: 1px solid {accent};
        width: 12px;
        margin-top: -4px;
        margin-bottom: -4px;
        border-radius: 6px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: #e2e8f0;
        border: 1px solid {border};
        border-radius: 2px;
        text-align: center;
        color: {text_primary};
        font-size: 8pt;
        font-weight: bold;
    }}
    QProgressBar::chunk {{
        background-color: {accent};
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {status_bg};
        color: {text_muted};
        border-top: 1px solid {border};
        padding: 2px 8px;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 8.5pt;
    }}
    QStatusBar QLabel {{
        padding: 0px 8px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {scroll_bg};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {scroll_handle};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #94a3b8;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
