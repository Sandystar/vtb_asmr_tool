from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
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

from spider_vtbasmr_gui.services.resource_transfer_service import TransferResourceItem
from spider_vtbasmr_gui.ui.widgets import ResourceItemCard, SectionCard, StatusLabel


class ResourceTransferPage(QWidget):
    login_requested = Signal()
    parse_requested = Signal(str)
    transfer_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        self._default_log_dir = Path.cwd()
        self._resource_items: list[TransferResourceItem] = []
        self._build()

    @property
    def resource_items(self) -> list[TransferResourceItem]:
        return list(self._resource_items)

    def set_default_log_directory(self, path: Path) -> None:
        self._default_log_dir = path

    def set_resource_items(self, items: list[TransferResourceItem]) -> None:
        self._resource_items = list(items)
        self._count.setText(f"资源 {len(items)}")
        self._transfer_button.setDisabled(not items)
        self._rebuild_items()

    def set_log_file_path(self, path: str) -> None:
        self._log_path.setText(path)

    def set_busy(self, busy: bool) -> None:
        for control in self._controls:
            control.setDisabled(busy)
        if not busy:
            self._transfer_button.setDisabled(not self._resource_items)

    def show_login_status(self, message: str, tone: str = "default") -> None:
        self._login_status.show_status(message, tone)

    def show_parse_status(self, message: str, tone: str = "default") -> None:
        self._parse_status.show_status(message, tone)

    def show_transfer_status(self, message: str, tone: str = "default") -> None:
        self._transfer_status.show_status(message, tone)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        columns = QWidget()
        columns.setObjectName("contentPanel")
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(16)

        actions = SectionCard("操作")
        self._login_button = QPushButton("刷新 FNOS 认证")
        self._login_button.clicked.connect(self.login_requested.emit)
        actions.body_layout.addWidget(self._login_button)
        self._login_status = StatusLabel("使用当前本地认证配置。")
        actions.body_layout.addWidget(self._login_status)
        label = QLabel("抓取日志")
        label.setObjectName("fieldLabel")
        actions.body_layout.addWidget(label)
        row = QWidget()
        row.setObjectName("fieldRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        self._log_path = QLineEdit()
        choose_button = QPushButton("选择")
        choose_button.setObjectName("secondaryButton")
        choose_button.clicked.connect(self._choose_log)
        row_layout.addWidget(self._log_path, 1)
        row_layout.addWidget(choose_button)
        actions.body_layout.addWidget(row)
        parse_button = QPushButton("解析日志")
        parse_button.setObjectName("secondaryButton")
        parse_button.clicked.connect(lambda: self.parse_requested.emit(self._log_path.text().strip()))
        actions.body_layout.addWidget(parse_button)
        self._parse_status = StatusLabel("等待解析日志。")
        actions.body_layout.addWidget(self._parse_status)
        self._transfer_button = QPushButton("转存并提交下载")
        self._transfer_button.setDisabled(True)
        self._transfer_button.clicked.connect(self.transfer_requested.emit)
        actions.body_layout.addWidget(self._transfer_button)
        self._transfer_status = StatusLabel("等待资源就绪。")
        actions.body_layout.addWidget(self._transfer_status)
        actions.body_layout.addStretch(1)
        columns_layout.addWidget(actions, 4)

        list_card = SectionCard("资源列表")
        self._count = QLabel("资源 0")
        self._count.setObjectName("countLabel")
        list_card.body_layout.addWidget(self._count)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll_content = QWidget()
        self._scroll_content.setObjectName("transparentPanel")
        self._items_layout = QVBoxLayout(self._scroll_content)
        self._items_layout.setContentsMargins(8, 8, 8, 8)
        self._items_layout.addStretch(1)
        self._scroll.setWidget(self._scroll_content)
        list_card.body_layout.addWidget(self._scroll, 1)
        columns_layout.addWidget(list_card, 5)
        layout.addWidget(columns, 1)
        self._controls = [self._login_button, self._log_path, choose_button, parse_button, self._transfer_button]

    def _choose_log(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择抓取日志",
            str(self._default_log_dir),
            "JSON Files (*.json)",
        )
        if path:
            self._log_path.setText(path)

    def _rebuild_items(self) -> None:
        while self._items_layout.count() > 1:
            item = self._items_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
        for resource in self._resource_items:
            self._items_layout.insertWidget(self._items_layout.count() - 1, ResourceItemCard(resource))