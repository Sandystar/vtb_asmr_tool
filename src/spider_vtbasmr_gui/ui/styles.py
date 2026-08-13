from __future__ import annotations


def build_application_stylesheet() -> str:
    return """
    QWidget {
        color: #f1f0ea;
        background: #171a1d;
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 14px;
    }
    QWidget#appRoot { background: #171a1d; }
    QWidget#sidebarRail {
        background: #0d0f10;
        border-right: 1px solid #2b3033;
    }
    QWidget#sidebarBrand, QWidget#mainHeader, QWidget#pageSurface,
    QWidget#transparentPanel, QWidget#contentPanel, QWidget#fieldRow,
    QWidget#toolbar, QWidget#workspace, QWidget#progressMetrics,
    QWidget#progressMetric, QWidget#taskParameters, QWidget#vtbSelection {
        background: transparent;
        border: none;
    }
    QLabel { background: transparent; }
    QLabel#brandName {
        color: #f1f0ea;
        font-size: 19px;
        font-weight: 800;
        letter-spacing: 1px;
    }
    QLabel#brandDescriptor {
        color: #777d7f;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
    }
    QWidget#workspace { background: #171a1d; }
    QLabel#pageTitle {
        color: #f6f4ee;
        font-size: 28px;
        font-weight: 800;
    }
    QLabel#pageDescription {
        color: #989d9e;
        font-size: 13px;
    }
    QPushButton {
        background: #e6a15c;
        color: #211810;
        border: 1px solid #e6a15c;
        border-radius: 7px;
        padding: 9px 15px;
        font-weight: 700;
    }
    QPushButton:hover { background: #f0b271; border-color: #f0b271; }
    QPushButton:pressed { background: #c98143; border-color: #c98143; }
    QPushButton:disabled { background: #343a3d; color: #777d7f; border-color: #343a3d; }
    QPushButton#secondaryButton {
        background: #252a2d;
        color: #d8d7d0;
        border: 1px solid #3a4144;
    }
    QPushButton#secondaryButton:hover { background: #30373a; border-color: #596164; }
    QPushButton#secondaryButton:pressed { background: #1f2426; }
    QPushButton#navigationButton {
        background: transparent;
        color: #979c9d;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 12px 10px;
        text-align: left;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton#navigationButton:hover {
        background: #191e20;
        color: #e5e3dc;
    }
    QPushButton#navigationButton:checked {
        background: #29231d;
        color: #f0b678;
        border-color: #60482f;
    }
    QPushButton#navigationButton:disabled { color: #4c5153; }
    QWidget#sectionCard {
        background: #1d2124;
        border: 1px solid #30363a;
        border-radius: 12px;
    }
    QWidget#sectionHeader, QFrame#sectionRule {
        background: transparent;
        border: none;
    }
    QFrame#sectionRule { color: #a9aca7; background: #a9aca7; max-height: 1px; }
    QWidget#itemCard {
        background: #151819;
        border: 1px solid #596164;
        border-radius: 4px;
    }
    QWidget#vtbTableRow {
        background: #171b1d;
        border: none;
        border-bottom: 1px solid #434a4d;
    }
    QWidget#vtbTableRow[lastRow="true"] { border-bottom: none; }
    QLabel#vtbTableLabel {
        background: #24292c;
        color: #e0ded7;
        border: none;
        border-right: 1px solid #596164;
        padding: 8px 10px;
        font-weight: 700;
    }
    QLineEdit#vtbTableInput {
        background: #111416;
        border: 1px solid #3f474a;
        border-radius: 7px;
        margin: 4px 7px;
        padding: 5px 9px;
    }
    QLineEdit#vtbTableInput:hover {
        background: #171b1d;
        border-color: #626b6e;
    }
    QLineEdit#vtbTableInput:focus {
        background: #1b1f21;
        border: 1px solid #e6a15c;
    }
    QWidget#vtbTableActionCell {
        background: #1b1f21;
        border: none;
        border-left: 1px solid #596164;
    }
    QPushButton#vtbTableDeleteButton {
        background: #292e31;
        color: #d8d7d0;
        border: 1px solid #4d5558;
        border-radius: 4px;
        padding: 5px 11px;
    }
    QPushButton#vtbTableDeleteButton:hover {
        background: #3a2928;
        color: #edaaa5;
        border-color: #87504d;
    }
    QLabel#sectionTitle {
        color: #f1f0ea;
        font-size: 16px;
        font-weight: 750;
    }
    QLabel#helperText, QLabel#appSubtitle { color: #8f9596; font-size: 13px; }
    QLabel#fieldLabel, QLabel#itemTitle { color: #dcdad3; font-weight: 650; }
    QLabel#linkText { color: #e6a15c; font-size: 12px; }
    QLabel#countLabel { color: #a5aaa9; font-weight: 650; }
    QLabel#progressMetricTitle { color: #8f9596; font-size: 12px; }
    QLabel#progressMetricValue { color: #f1f0ea; font-size: 16px; font-weight: 750; }
    QLabel#statusLabel { color: #8f9596; font-size: 12px; }
    QLabel#statusLabel[statusTone="success"] { color: #9dd5a7; }
    QLabel#statusLabel[statusTone="warning"] { color: #e2c077; }
    QLabel#statusLabel[statusTone="error"] { color: #e28c87; }
    QLineEdit, QComboBox, QListWidget {
        background: #151819;
        color: #eeece5;
        border: 1px solid #3a4144;
        border-radius: 7px;
        padding: 8px 10px;
        selection-background-color: #8c5a31;
        selection-color: #fff8ed;
    }
    QLineEdit:hover, QComboBox:hover, QListWidget:hover { border-color: #555d60; }
    QLineEdit:focus, QComboBox:focus, QListWidget:focus { border-color: #e6a15c; }
    QLineEdit:disabled, QComboBox:disabled { color: #707678; background: #1c2022; }
    QListWidget::item { padding: 7px; border-radius: 5px; }
    QListWidget::item:hover { background: #252b2d; }
    QListWidget::item:selected { background: #3d3023; color: #f0b678; }
    QProgressBar#crawlProgressBar {
        min-height: 20px;
        background: #151819;
        color: #f1f0ea;
        border: 1px solid #3a4144;
        border-radius: 6px;
        text-align: center;
        font-size: 12px;
        font-weight: 700;
    }
    QProgressBar#crawlProgressBar::chunk {
        background: #e6a15c;
        border-radius: 5px;
    }
    QScrollArea {
        background: #151819;
        border: 1px solid #30363a;
        border-radius: 8px;
    }
    QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
    QScrollBar::handle:vertical { background: #4a5357; border-radius: 5px; min-height: 24px; }
    QScrollBar::handle:vertical:hover { background: #687276; }
    """
