from . import theme as t


def STYLE_QSS() -> str:
    return f"""
    /* YT Stream 247 — Qt theme aligned with ytstream247.com */

    QMainWindow {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.BRAND_900},
            stop:0.5 {t.BRAND_900},
            stop:1 {t.BRAND_800});
    }}

    QWidget {{
        color: {t.TEXT_SECONDARY};
        font-family: "Inter Variable", "Inter", "SF Pro Display",
                     "Segoe UI Variable Display", "Segoe UI",
                     "Roboto", "Helvetica Neue",
                     -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px;
        font-weight: 400;
        letter-spacing: 0.01em;
    }}

    QWidget#root {{
        background: transparent;
    }}

    QLabel#brandTitleWordmark {{
        background: transparent;
        padding: 16px 0 12px 0;
        margin-left: 6px;
        border: none;
    }}

    QLabel#brandTitleSuffix {{
        font-size: 20px;
        font-weight: 500;
        color: {t.MUTED};
        letter-spacing: -0.01em;
        background: transparent;
        padding: 16px 0 12px 0;
        margin-left: 10px;
        border: none;
    }}

    QLabel#sectionLabel {{
        color: {t.TEXT};
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.4px;
        margin-top: 4px;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1px solid {t.BORDER_STRONG};
        line-height: 1.4;
    }}

    QLabel#statusLabel {{
        color: {t.TEXT_SECONDARY};
        font-weight: 600;
        font-size: 14px;
        padding: 10px 14px;
        letter-spacing: 0.02em;
        line-height: 1.5;
        background-color: {t.PRIMARY_08};
        border-left: 3px solid {t.PRIMARY_60};
        border-radius: 6px;
    }}

    QLabel#gpuStatusLabel {{
        color: {t.MUTED_DARK};
        font-size: 12px;
        font-style: italic;
        padding-left: 6px;
        margin-top: -4px;
    }}

    QLabel#modeHelpLabel {{
        color: {t.TEXT_SECONDARY};
        font-size: 12px;
        line-height: 1.35;
        padding: 6px 4px 4px 4px;
        margin-top: 0px;
        border: none;
        background: transparent;
    }}

    QFrame#card {{
        background-color: {t.SURFACE_CARD};
        border: 1px solid {t.BORDER_SUBTLE};
        border-top: 2px solid {t.SURFACE_CARD_TOP};
        border-radius: {t.RADIUS_CARD}px;
        padding: 8px;
    }}

    QListWidget#dropQueueList {{
        background-color: {t.SURFACE_DROPZONE};
        border: {t.DROPZONE_BORDER_PX}px dashed {t.DROPZONE_BORDER};
        border-radius: {t.RADIUS_BLOB}px;
        padding: 16px;
        outline: none;
        selection-background-color: transparent;
    }}
    QListWidget#dropQueueList[dropHover="true"] {{
        border: {t.DROPZONE_BORDER_PX}px dashed {t.DROPZONE_BORDER};
        background-color: {t.SURFACE_DROPZONE};
    }}
    QListWidget#dropQueueList::item {{
        background-color: {t.SURFACE_LIST_ITEM};
        border: 1px solid {t.BORDER_STRONG};
        border-radius: {t.RADIUS_ITEM}px;
        padding: 14px 18px;
        margin: 5px 4px;
        color: {t.TEXT_SECONDARY};
        font-weight: 500;
        font-size: 14px;
        min-height: 32px;
        letter-spacing: 0.01em;
    }}
    QListWidget#dropQueueList::item:hover {{
        background-color: {t.PANEL_HOVER};
        border-color: {t.PRIMARY_55};
    }}
    QListWidget#dropQueueList::item:selected {{
        background-color: {t.SURFACE_LIST_ITEM};
        border: 1px solid {t.BORDER_STRONG};
        color: {t.TEXT_SECONDARY};
        font-weight: 500;
    }}

    QLineEdit, QSpinBox, QComboBox {{
        background-color: {t.SURFACE_INSET};
        border: 1.5px solid {t.BORDER_STRONG};
        border-radius: {t.RADIUS_INPUT}px;
        padding: 12px 16px;
        color: {t.TEXT};
        font-weight: 500;
        font-size: 14px;
        letter-spacing: 0.01em;
        selection-background-color: {t.PRIMARY_40};
        selection-color: {t.TEXT};
    }}
    QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
        border-color: {t.BORDER_LIGHT};
        background-color: {t.SURFACE_INSET};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1.5px solid {t.PRIMARY_70};
        background-color: {t.SURFACE_INSET};
        outline: none;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
        background-color: transparent;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {t.MUTED};
        margin-right: 10px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #111827;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 0px;
        selection-background-color: #7f1d1d;
        selection-color: #FFFFFF;
        color: #CBD5E1;
        padding: 0px;
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 11px 16px;
        min-height: 38px;
        border-radius: 0px;
        background-color: #111827;
        color: #CBD5E1;
        border: none;
    }}
    QComboBox QAbstractItemView::item:hover,
    QComboBox QAbstractItemView::item:focus {{
        background-color: #374151;
        color: #FFFFFF;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: #7f1d1d;
        color: #FFFFFF;
    }}

    QComboBox#modeCombo, QComboBox#tierCombo {{
        min-height: 36px;
        font-weight: 600;
        font-size: 15px;
        padding-top: 9px;
        padding-bottom: 9px;
    }}

    QScrollArea#settingsScroll {{
        background: transparent;
        border: none;
    }}
    QScrollArea#settingsScroll > QWidget {{
        background: transparent;
        border: none;
    }}

    QPushButton#btnStream {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.PRIMARY_15},
            stop:1 {t.PRIMARY_10});
        border: 1.5px solid {t.PRIMARY_45};
        border-radius: {t.RADIUS_PILL}px;
        padding: 8px 18px 8px 14px;
        color: {t.PRIMARY_LIGHT};
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.03em;
        margin-right: 8px;
        min-height: 0px;
    }}
    QPushButton#btnStream:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.PRIMARY_25},
            stop:1 {t.PRIMARY_22});
        border-color: {t.PRIMARY_60};
        color: {t.TEXT};
    }}
    QPushButton#btnStream:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.PRIMARY_35},
            stop:1 {t.PRIMARY_30});
        border-color: {t.PRIMARY_70};
        color: {t.TEXT};
    }}

    QComboBox#langCombo {{
        background-color: {t.PRIMARY_10};
        border: 1.5px solid {t.PRIMARY_40};
        border-radius: {t.RADIUS_PILL}px;
        padding: 8px 14px;
        padding-right: 32px;
        color: {t.PRIMARY_LIGHT};
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.02em;
    }}
    QComboBox#langCombo:hover {{
        background-color: {t.PRIMARY_15};
        border-color: {t.PRIMARY_55};
        color: {t.TEXT};
    }}
    QComboBox#langCombo:focus {{
        border: 1.5px solid {t.PRIMARY_70};
        background-color: {t.PRIMARY_12};
        outline: none;
    }}
    QComboBox#langCombo::drop-down {{
        border: none;
        width: 28px;
        background-color: transparent;
    }}
    QComboBox#langCombo::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {t.PRIMARY};
        margin-right: 12px;
    }}
    QComboBox#langCombo QAbstractItemView {{
        background-color: #0B0F19;
        border: 1px solid rgba(255,0,0,0.35);
        border-radius: 0px;
        selection-background-color: #7f1d1d;
        selection-color: #FFFFFF;
        padding: 0px;
        color: #FF4B4B;
        outline: none;
    }}
    QComboBox#langCombo QAbstractItemView::item {{
        padding: 10px 16px;
        min-height: 36px;
        background-color: #0B0F19;
        color: #FF4B4B;
        border: none;
    }}
    QComboBox#langCombo QAbstractItemView::item:hover,
    QComboBox#langCombo QAbstractItemView::item:focus {{
        background-color: #1F2937;
        color: #FFFFFF;
    }}
    QComboBox#langCombo QAbstractItemView::item:selected {{
        background-color: #7f1d1d;
        color: #FFFFFF;
    }}

    QPushButton {{
        background-color: {t.NEUTRAL_BTN_BG};
        color: {t.TEXT};
        border: 1px solid {t.NEUTRAL_BTN_BORDER};
        border-radius: {t.RADIUS_BTN}px;
        padding: 10px 18px;
        font-weight: 600;
        font-size: 14px;
        min-height: 24px;
        letter-spacing: 0.02em;
    }}
    QPushButton:hover {{
        background-color: {t.NEUTRAL_BTN_HOVER};
        border-color: {t.NEUTRAL_BTN_HOVER_B};
    }}
    QPushButton:pressed {{
        background-color: {t.NEUTRAL_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: {t.NEUTRAL_DISABLED_BG};
        border-color: {t.NEUTRAL_DISABLED_BR};
        color: {t.NEUTRAL_DISABLED_FG};
    }}

    QPushButton#btnBrowse {{
        padding: 0px;
        background-color: {t.INFO_15};
        border: 1.5px solid {t.INFO_45};
    }}
    QPushButton#btnBrowse:hover {{
        background-color: {t.INFO_28};
        border-color: {t.INFO_65};
    }}
    QPushButton#btnBrowse:pressed {{
        background-color: {t.INFO_35};
    }}

    QPushButton#btnAdd, QPushButton#btnPaste {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.INFO_40},
            stop:1 {t.INFO_50});
        border: 1.5px solid {t.INFO_60};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        color: {t.INFO_LIGHT};
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    QPushButton#btnAdd:hover, QPushButton#btnPaste:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.INFO_50},
            stop:1 {t.INFO_60});
        border-color: {t.INFO_85};
        color: {t.INFO_HOVER_FG};
    }}
    QPushButton#btnAdd:pressed, QPushButton#btnPaste:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.INFO_35},
            stop:1 {t.INFO_45});
    }}
    QPushButton#btnAdd:disabled, QPushButton#btnPaste:disabled {{
        background: {t.NEUTRAL_DISABLED_BG};
        border-color: {t.NEUTRAL_DISABLED_BR};
        color: {t.NEUTRAL_DISABLED_FG};
    }}

    QPushButton#btnClear, QPushButton#btnStop {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.ERR_35},
            stop:1 {t.ERR_45});
        border: 1.5px solid {t.ERR_60};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        color: {t.ERROR_SOFT};
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    QPushButton#btnClear:hover, QPushButton#btnStop:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.ERR_50},
            stop:1 {t.ERR_60});
        border-color: {t.ERR_85};
        color: {t.ERROR_HOVER_FG};
    }}
    QPushButton#btnClear:pressed, QPushButton#btnStop:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.ERR_40},
            stop:1 rgba(185, 28, 28, 0.5));
    }}
    QPushButton#btnClear:disabled, QPushButton#btnStop:disabled {{
        background: {t.NEUTRAL_DISABLED_BG};
        border-color: {t.NEUTRAL_DISABLED_BR};
        color: {t.NEUTRAL_DISABLED_FG};
    }}

    QPushButton#btnStart {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {t.PRIMARY},
            stop:0.5 {t.PRIMARY_DARK},
            stop:1 {t.PRIMARY_DARK});
        border: 1px solid {t.PRIMARY_45};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        color: {t.TEXT};
        font-size: 16px;
        font-weight: 700;
        padding: 12px 24px;
        border-radius: 14px;
        letter-spacing: 0.05em;
    }}
    QPushButton#btnStart:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {t.PRIMARY_LIGHT},
            stop:0.5 {t.PRIMARY},
            stop:1 {t.PRIMARY_DARK});
        border: 1px solid {t.PRIMARY_60};
    }}
    QPushButton#btnStart:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {t.PRIMARY_DARK},
            stop:0.5 {t.PRIMARY_PRESS_MID},
            stop:1 {t.PRIMARY_PRESS_END});
    }}
    QPushButton#btnStart:disabled {{
        background: {t.NEUTRAL_DISABLED_BG};
        color: {t.NEUTRAL_DISABLED_FG};
        border: 1px solid {t.NEUTRAL_DISABLED_BR};
    }}

    QPushButton#advToggle {{
        background: transparent;
        border: none;
        color: {t.MUTED};
        text-align: left;
        padding: 8px 0;
        font-weight: 500;
    }}
    QPushButton#advToggle:hover {{
        color: {t.TEXT_SECONDARY};
        text-decoration: underline;
    }}

    QCheckBox {{
        spacing: 12px;
        color: {t.TEXT_SECONDARY};
        font-weight: 500;
        font-size: 14px;
        padding: 8px 0;
        letter-spacing: 0.01em;
    }}
    QCheckBox::indicator {{
        width: 22px;
        height: 22px;
        border-radius: 7px;
        border: 2px solid {t.BORDER_LIGHT};
        background-color: {t.SURFACE_INSET};
    }}
    QCheckBox::indicator:hover {{
        border-color: {t.PRIMARY_60};
        background-color: rgba(31, 41, 55, 0.95);
    }}
    QCheckBox::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.PRIMARY_LIGHT},
            stop:1 {t.PRIMARY_DARK});
        border-color: {t.PRIMARY};
        image: none;
    }}
    QCheckBox::indicator:checked:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.PRIMARY},
            stop:1 {t.PRIMARY_DARK});
    }}
    QCheckBox::indicator:disabled {{
        background-color: {t.NEUTRAL_DISABLED_BG};
        border-color: {t.NEUTRAL_DISABLED_BR};
    }}

    QTextEdit {{
        background-color: {t.SURFACE_INSET};
        border: 1.5px solid {t.BORDER_STRONG};
        border-radius: {t.RADIUS_INPUT}px;
        font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", monospace;
        font-size: 13px;
        color: {t.MUTED};
        padding: 10px;
        selection-background-color: {t.PRIMARY_40};
    }}

    QProgressBar {{
        background-color: {t.SURFACE_INSET};
        border: 1.5px solid {t.PRIMARY_25};
        border-radius: {t.RADIUS_PROGRESS}px;
        text-align: center;
        height: 36px;
        color: {t.TEXT_SECONDARY};
        font-weight: 600;
        font-size: 13px;
        padding: 4px;
        letter-spacing: 0.02em;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.PRIMARY_LIGHT},
            stop:0.5 {t.PRIMARY},
            stop:1 {t.PRIMARY_DARK});
        border-radius: {t.RADIUS_CHUNK}px;
        margin: 2px;
    }}

    QScrollBar:vertical {{
        background-color: {t.SCROLL_TRACK};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {t.SCROLL_HANDLE};
        border-radius: 5px;
        min-height: 40px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {t.SCROLL_HANDLE_HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {t.SCROLL_TRACK};
        height: 10px;
        border-radius: 5px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {t.SCROLL_HANDLE};
        border-radius: 5px;
        min-width: 40px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {t.SCROLL_HANDLE_HOVER};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QMenu {{
        background-color: {t.SURFACE_MENU};
        border: 1px solid {t.BORDER_STRONG};
        border-radius: 12px;
        padding: 6px;
        color: {t.TEXT_SECONDARY};
    }}
    QMenu::item {{
        padding: 8px 28px 8px 16px;
        border-radius: 8px;
        margin: 2px 4px;
        font-size: 13px;
    }}
    QMenu::item:selected {{
        background-color: {t.PRIMARY_25};
        color: {t.TEXT};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {t.BORDER_STRONG};
        margin: 4px 8px;
    }}

    QToolTip {{
        background-color: {t.SURFACE_MENU};
        border: 1px solid {t.BORDER_STRONG};
        border-radius: 8px;
        color: {t.TEXT_SECONDARY};
        font-size: 12px;
        padding: 6px 10px;
    }}

    QMessageBox {{
        background-color: {t.BRAND_800};
    }}
    QMessageBox QLabel {{
        color: {t.TEXT_SECONDARY};
        font-size: 14px;
    }}
    QMessageBox QPushButton {{
        min-width: 80px;
        padding: 8px 20px;
    }}
    """
