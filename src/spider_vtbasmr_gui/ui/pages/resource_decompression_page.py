from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from spider_vtbasmr_gui.services.decompression_service import DiscoveredArchiveFile
from spider_vtbasmr_gui.ui.widgets import ArchivePreviewCard, SectionCard, StatusLabel


@dataclass(frozen=True, slots=True)
class DecompressionRequest:
    source_root: str
    target_root: str
    password: str | None


class ResourceDecompressionPage(QWidget):
    preview_requested = Signal(object)
    decompress_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        self._files: list[DiscoveredArchiveFile] = []
        self._build()

    def set_files(self, files: list[DiscoveredArchiveFile]) -> None:
        self._files = list(files)
        self._count.setText(f"待解压 {len(files)}")
        self._rebuild_items()

    def set_busy(self, busy: bool) -> None:
        for control in self._controls:
            control.setDisabled(busy)

    def show_status(self, message: str, tone: str = "default") -> None:
        self._status.show_status(message, tone)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        columns = QWidget()
        columns.setObjectName("contentPanel")
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(16)
        actions = SectionCard("解压参数")
        self._source, source_button = self._directory_field(actions, "源目录")
        self._target, target_button = self._directory_field(actions, "目标目录")
        label = QLabel("本次密码（可选）")
        label.setObjectName("fieldLabel")
        actions.body_layout.addWidget(label)
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        actions.body_layout.addWidget(self._password)
        preview_button = QPushButton("预览文件")
        preview_button.setObjectName("secondaryButton")
        preview_button.clicked.connect(lambda: self.preview_requested.emit(self._request()))
        decompress_button = QPushButton("开始解压")
        decompress_button.clicked.connect(lambda: self.decompress_requested.emit(self._request()))
        actions.body_layout.addWidget(preview_button)
        actions.body_layout.addWidget(decompress_button)
        self._status = StatusLabel("等待选择目录。")
        actions.body_layout.addWidget(self._status)
        actions.body_layout.addStretch(1)
        columns_layout.addWidget(actions, 4)

        preview = SectionCard("预览")
        self._count = QLabel("待解压 0")
        self._count.setObjectName("countLabel")
        preview.body_layout.addWidget(self._count)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("transparentPanel")
        self._items_layout = QVBoxLayout(content)
        self._items_layout.setContentsMargins(8, 8, 8, 8)
        self._items_layout.addStretch(1)
        scroll.setWidget(content)
        preview.body_layout.addWidget(scroll, 1)
        columns_layout.addWidget(preview, 5)
        layout.addWidget(columns, 1)
        self._controls = [
            self._source,
            self._target,
            self._password,
            source_button,
            target_button,
            preview_button,
            decompress_button,
        ]

    def _directory_field(self, card: SectionCard, title: str) -> tuple[QLineEdit, QPushButton]:
        label = QLabel(title)
        label.setObjectName("fieldLabel")
        card.body_layout.addWidget(label)
        row = QWidget()
        row.setObjectName("fieldRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit()
        button = QPushButton("选择")
        button.setObjectName("secondaryButton")
        button.clicked.connect(lambda: self._choose_directory(line_edit))
        row_layout.addWidget(line_edit, 1)
        row_layout.addWidget(button)
        card.body_layout.addWidget(row)
        return line_edit, button

    def _choose_directory(self, line_edit: QLineEdit) -> None:
        current = Path(line_edit.text().strip()) if line_edit.text().strip() else Path.cwd()
        path = QFileDialog.getExistingDirectory(self, "选择目录", str(current))
        if path:
            line_edit.setText(path)

    def _request(self) -> DecompressionRequest:
        return DecompressionRequest(
            source_root=self._source.text().strip(),
            target_root=self._target.text().strip(),
            password=self._password.text().strip() or None,
        )

    def _rebuild_items(self) -> None:
        while self._items_layout.count() > 1:
            item = self._items_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
        for file in self._files:
            self._items_layout.insertWidget(self._items_layout.count() - 1, ArchivePreviewCard(file))