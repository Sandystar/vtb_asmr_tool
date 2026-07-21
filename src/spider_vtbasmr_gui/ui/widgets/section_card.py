from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SectionCard(QWidget):
    def __init__(self, title: str, description: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        if description:
            description_label = QLabel(description)
            description_label.setObjectName("helperText")
            description_label.setWordWrap(True)
            layout.addWidget(description_label)

        body = QWidget()
        body.setObjectName("transparentPanel")
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        layout.addWidget(body)