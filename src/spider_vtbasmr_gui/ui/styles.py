from __future__ import annotations


def build_application_stylesheet() -> str:
    return """
    QWidget {
        color: #e7edf5;
        background: #11161d;
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 14px;
    }
    QWidget#appRoot { background: #0d1218; }
    QWidget#pageRoot, QWidget#transparentPanel, QWidget#contentPanel,
    QWidget#fieldRow, QWidget#toolbar { background: transparent; border: none; }
    QWidget#pageContainer {
        background: #161d26;
        border: 1px solid #293442;
        border-radius: 20px;
    }
    QWidget#sectionCard {
        background: #1b2430;
        border: 1px solid #334152;
        border-radius: 16px;
    }
    QWidget#itemCard {
        background: #141c25;
        border: 1px solid #2b3948;
        border-radius: 12px;
    }
    QLabel { background: transparent; }
    QLabel#appTitle { font-size: 27px; font-weight: 700; color: #f5f8fc; }
    QLabel#appSubtitle, QLabel#helperText { color: #91a0b2; font-size: 13px; }
    QLabel#sectionTitle { font-size: 17px; font-weight: 700; color: #f5f8fc; }
    QLabel#fieldLabel, QLabel#itemTitle { font-weight: 600; color: #dfe8f2; }
    QLabel#linkText { color: #78b7ff; font-size: 12px; }
    QLabel#countLabel { color: #91a0b2; font-weight: 600; }
    QLabel#statusLabel { color: #91a0b2; font-size: 12px; }
    QLabel#statusLabel[statusTone="success"] { color: #75d69c; }
    QLabel#statusLabel[statusTone="warning"] { color: #e6c36a; }
    QLabel#statusLabel[statusTone="error"] { color: #ff8c88; }
    QLineEdit, QComboBox, QListWidget {
        background: #101720;
        color: #e7edf5;
        border: 1px solid #354456;
        border-radius: 9px;
        padding: 8px 10px;
        selection-background-color: #3788f2;
    }
    QLineEdit:focus, QComboBox:focus, QListWidget:focus { border-color: #5ca4ff; }
    QListWidget::item { padding: 7px; border-radius: 7px; }
    QListWidget::item:hover { background: #1d2a38; }
    QPushButton {
        background: #3281e8;
        color: white;
        border: none;
        border-radius: 9px;
        padding: 9px 15px;
        font-weight: 700;
    }
    QPushButton:hover { background: #4592f2; }
    QPushButton:pressed { background: #256ac0; }
    QPushButton:disabled { background: #394452; color: #8491a0; }
    QPushButton#secondaryButton {
        background: #242f3c;
        border: 1px solid #3b4a5d;
    }
    QPushButton#secondaryButton:hover { background: #2d3a49; }
    QPushButton#navigationButton {
        background: transparent;
        color: #a8b5c4;
        border: 1px solid transparent;
        padding: 10px 15px;
    }
    QPushButton#navigationButton:hover { background: #18212b; color: #e7edf5; }
    QPushButton#navigationButton:checked {
        background: #213751;
        color: #8fc2ff;
        border-color: #345d88;
    }
    QScrollArea {
        background: #101720;
        border: 1px solid #2e3a49;
        border-radius: 11px;
    }
    QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
    QScrollBar::handle:vertical { background: #3a4a5c; border-radius: 5px; min-height: 24px; }
    QStatusBar { background: #0a0e13; color: #91a0b2; border-top: 1px solid #27313d; }
    """