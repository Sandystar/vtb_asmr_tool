from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget


class StatusLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("statusLabel")
        self.setWordWrap(True)

    def show_status(self, message: str, tone: str = "default") -> None:
        self.setText(message)
        self.setProperty("statusTone", tone)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()