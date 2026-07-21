from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from spider_vtbasmr_gui.config.app_config import AppConfig
from spider_vtbasmr_gui.ui.widgets import SectionCard, StatusLabel


class BasicConfigPage(QWidget):
    save_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._controls: list[QWidget] = []
        self._build()

    def set_config(self, config: AppConfig) -> None:
        self._base_path.setText(str(config.spider_base_config_path or ""))
        self._vtb_path.setText(str(config.spider_vtb_config_path or ""))
        self._netdisk_path.setText(str(config.netdisk_config_path or ""))
        self._transfer_root.setText(config.transfer_root_dir or "")
        self._nas_dir.setText(config.nas_download_dir or "")
        self._seven_zip.setText(str(config.seven_zip_path or ""))
        self._password.setText(config.decompression_password or "")

    def current_config(self) -> AppConfig:
        return AppConfig(
            spider_base_config_path=self._read_path(self._base_path),
            spider_vtb_config_path=self._read_path(self._vtb_path),
            netdisk_config_path=self._read_path(self._netdisk_path),
            transfer_root_dir=self._read_text(self._transfer_root),
            nas_download_dir=self._read_text(self._nas_dir),
            seven_zip_path=self._read_path(self._seven_zip),
            decompression_password=self._read_text(self._password),
        )

    def set_busy(self, busy: bool) -> None:
        for control in self._controls:
            control.setDisabled(busy)

    def show_status(self, message: str, tone: str = "default") -> None:
        self._status.show_status(message, tone)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        header = SectionCard(
            "基本配置",
            "工程内路径会保存为相对路径；保存后运行服务立即刷新，不需要重启。",
        )
        layout.addWidget(header)

        columns = QWidget()
        columns.setObjectName("contentPanel")
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(16)

        runtime_card = SectionCard("运行配置", "三个 JSON 文件只在本地 .data 中使用。")
        self._base_path = self._add_file_field(runtime_card, "抓取基础配置")
        self._vtb_path = self._add_file_field(runtime_card, "VTB 配置")
        self._netdisk_path = self._add_file_field(runtime_card, "FNOS 配置")
        runtime_card.body_layout.addStretch(1)
        columns_layout.addWidget(runtime_card, 1)

        processing_card = SectionCard("资源处理")
        self._transfer_root = self._add_text_field(processing_card, "网盘转存目录", "/vtbasmr")
        self._nas_dir = self._add_text_field(processing_card, "NAS 下载目录", "/vol1/downloads")
        self._seven_zip = self._add_file_field(
            processing_card,
            "7z 可执行文件",
            file_filter="Executable (*.exe);;All Files (*)",
        )
        self._password = self._add_text_field(processing_card, "默认解压密码", "可以留空")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        columns_layout.addWidget(processing_card, 1)
        layout.addWidget(columns, 1)

        action_card = SectionCard("保存")
        self._save_button = QPushButton("保存并应用")
        self._save_button.clicked.connect(lambda: self.save_requested.emit(self.current_config()))
        action_card.body_layout.addWidget(self._save_button)
        self._status = StatusLabel("等待加载配置。")
        action_card.body_layout.addWidget(self._status)
        layout.addWidget(action_card)
        self._controls.append(self._save_button)

    def _add_file_field(
        self,
        card: SectionCard,
        label: str,
        *,
        file_filter: str = "JSON Files (*.json);;All Files (*)",
    ) -> QLineEdit:
        card.body_layout.addWidget(self._label(label))
        row = QWidget()
        row.setObjectName("fieldRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        line_edit = QLineEdit()
        button = QPushButton("浏览")
        button.setObjectName("secondaryButton")
        button.clicked.connect(lambda: self._choose_file(line_edit, file_filter))
        row_layout.addWidget(line_edit, 1)
        row_layout.addWidget(button)
        card.body_layout.addWidget(row)
        self._controls.extend([line_edit, button])
        return line_edit

    def _add_text_field(self, card: SectionCard, label: str, placeholder: str) -> QLineEdit:
        card.body_layout.addWidget(self._label(label))
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        card.body_layout.addWidget(line_edit)
        self._controls.append(line_edit)
        return line_edit

    def _choose_file(self, line_edit: QLineEdit, file_filter: str) -> None:
        current = Path(line_edit.text().strip()) if line_edit.text().strip() else Path.cwd()
        initial = current.parent if current.is_file() else current
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", str(initial), file_filter)
        if path:
            line_edit.setText(path)

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    @staticmethod
    def _read_text(line_edit: QLineEdit) -> str | None:
        return line_edit.text().strip() or None

    @classmethod
    def _read_path(cls, line_edit: QLineEdit) -> Path | None:
        text = cls._read_text(line_edit)
        return Path(text) if text else None