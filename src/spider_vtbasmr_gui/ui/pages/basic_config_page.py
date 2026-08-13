from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from spider_vtbasmr.manager.base_config import SpiderBaseConfig
from spider_vtbasmr_gui.config.app_config import AppConfig
from spider_vtbasmr_gui.config.fnos_config import FnosConfig, FnosCredential
from spider_vtbasmr_gui.config.seven_zip_config import SevenZipConfig
from spider_vtbasmr_gui.config.vtb_list_config import VtbListConfig, VtbListItem
from spider_vtbasmr_gui.ui.widgets import SectionCard, StatusLabel, VtbListItemEditor


class BasicConfigPage(QWidget):
    save_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._controls: list[QWidget] = []
        self._storage_state: dict[str, object] | None = None
        self._fnos_config: FnosConfig | None = None
        self._vtb_item_editors: list[VtbListItemEditor] = []
        self._build()

    def set_config(self, config: AppConfig) -> None:
        self._fnos_config = config.fnos_config
        fnos = config.fnos_config or FnosConfig()
        seven_zip = config.seven_zip_config or SevenZipConfig()
        self._transfer_root.setText(fnos.transfer_root_dir or "")
        self._nas_dir.setText(fnos.nas_download_dir or "")
        self._seven_zip.setText(self._display_working_path(seven_zip.executable_path))
        self._password.setText(seven_zip.default_password or "")

        base_config = config.spider_base_config
        self._login_url.setText(base_config.login_url if base_config else "")
        self._username.setText(base_config.username if base_config else "")
        self._password_login.setText(base_config.password if base_config else "")
        credential = fnos.credential
        self._fnos_url.setText(credential.base_url or "")
        self._fnos_username.setText(credential.username or "")
        self._fnos_password.setText(credential.password or "")
        self._log_dir.setText(base_config.log_dir if base_config else ".data/logs")
        self._set_markers(base_config.resource_link_markers if base_config else ())
        self.set_vtb_list_config(config.vtb_list_config or VtbListConfig())
        self._storage_state = (
            dict(base_config.storage_state)
            if base_config and base_config.storage_state
            else None
        )

    def current_config(self) -> AppConfig:
        base_config = SpiderBaseConfig(
            login_url=self._read_text(self._login_url),
            username=self._read_text(self._username),
            password=self._read_text(self._password_login),
            resource_link_markers=tuple(self._read_markers()),
            log_dir=self._read_text(self._log_dir),
            storage_state=self._storage_state,
        )
        return AppConfig(
            spider_base_config=base_config,
            vtb_list_config=self.current_vtb_list_config(),
            fnos_config=self._visible_fnos_config(),
            seven_zip_config=SevenZipConfig(
                executable_path=self._read_path(self._seven_zip),
                default_password=self._read_text(self._password),
            ),
        )

    def _visible_fnos_config(self) -> FnosConfig:
        existing = self._fnos_config or FnosConfig()
        credential = existing.credential
        return replace(
            existing,
            credential=FnosCredential(
                base_url=self._read_text(self._fnos_url),
                username=self._read_text(self._fnos_username),
                password=self._read_text(self._fnos_password),
                cookie=credential.cookie,
                verify_ssl=credential.verify_ssl,
                language=credential.language,
                appid=credential.appid,
                product=credential.product,
                device_id=credential.device_id,
            ),
            transfer_root_dir=self._read_text(self._transfer_root),
            nas_download_dir=self._read_text(self._nas_dir),
        )

    def set_vtb_list_config(self, config: VtbListConfig) -> None:
        for editor in self._vtb_item_editors:
            self._vtb_items_layout.removeWidget(editor)
            editor.deleteLater()
        self._vtb_item_editors.clear()
        for item in config.items:
            self._add_vtb_item(item)

    def current_vtb_list_config(self) -> VtbListConfig:
        return VtbListConfig(tuple(editor.current_item() for editor in self._vtb_item_editors))

    def set_busy(self, busy: bool) -> None:
        for control in self._controls:
            control.setDisabled(busy)
        for editor in self._vtb_item_editors:
            editor.setDisabled(busy)

    def show_status(self, message: str, tone: str = "default") -> None:
        self._status.show_status(message, tone)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("configScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("transparentPanel")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)
        content_layout.addWidget(self._build_spider_config_card())
        content_layout.addWidget(self._build_vtb_list_config_card())
        content_layout.addWidget(self._build_fnos_config_card())
        content_layout.addWidget(self._build_decompression_card())
        content_layout.addWidget(self._build_action_card())
        content_layout.addStretch(1)
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)

    def _build_spider_config_card(self) -> SectionCard:
        card = SectionCard("网站抓取配置")
        self._login_url = self._add_text_field(card, "网站登录链接", "https://...")
        self._username = self._add_text_field(card, "登录账号", "邮箱或用户名")
        self._password_login = self._add_text_field(card, "登录密码", "登录密码")
        self._password_login.setEchoMode(QLineEdit.EchoMode.Password)

        card.body_layout.addWidget(self._label("网盘链接前缀列表"))
        self._markers = QListWidget()
        self._markers.setObjectName("markerList")
        self._markers.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._markers.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._markers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._markers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        card.body_layout.addWidget(self._markers)

        self._log_dir = self._add_text_field(card, "日志保存文件夹", ".data/logs")
        self._controls.append(self._markers)
        return card

    def _build_vtb_list_config_card(self) -> SectionCard:
        card = SectionCard("抓取列表配置")
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._add_vtb_button = QPushButton("新增抓取目标")
        self._add_vtb_button.clicked.connect(lambda: self._add_vtb_item())
        toolbar_layout.addWidget(self._add_vtb_button)
        toolbar_layout.addStretch(1)
        card.body_layout.addWidget(toolbar)

        self._vtb_items = QWidget()
        self._vtb_items.setObjectName("transparentPanel")
        self._vtb_items_layout = QVBoxLayout(self._vtb_items)
        self._vtb_items_layout.setContentsMargins(0, 0, 0, 0)
        self._vtb_items_layout.setSpacing(14)
        card.body_layout.addWidget(self._vtb_items)
        self._controls.append(self._add_vtb_button)
        return card

    def _add_vtb_item(self, item: VtbListItem | None = None) -> VtbListItemEditor:
        editor = VtbListItemEditor(item)
        editor.remove_requested.connect(self._remove_vtb_item)
        self._vtb_items_layout.addWidget(editor)
        self._vtb_item_editors.append(editor)
        return editor

    def _remove_vtb_item(self, editor: VtbListItemEditor) -> None:
        if editor not in self._vtb_item_editors:
            return
        self._vtb_item_editors.remove(editor)
        self._vtb_items_layout.removeWidget(editor)
        editor.deleteLater()

    def _build_fnos_config_card(self) -> SectionCard:
        card = SectionCard("fnOS配置")
        self._fnos_url = self._add_text_field(card, "fnOS访问链接", "http://...")
        self._fnos_username = self._add_text_field(card, "fnOS登录用户名", "用户名")
        self._fnos_password = self._add_text_field(card, "fnOS登录密码", "登录密码")
        self._fnos_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._transfer_root = self._add_text_field(card, "网盘转存文件夹", "/00-vtbasmr.net")
        self._nas_dir = self._add_text_field(
            card,
            "下载保存文件夹",
            "/vol2/1000/UserData/Download/BaiduNetdisk/asmrdh.net",
        )
        return card

    def _build_decompression_card(self) -> SectionCard:
        card = SectionCard("解压配置")
        self._seven_zip = self._add_text_field(card, "7z程序路径", "")
        self._password = self._add_text_field(card, "默认解压密码", "可以留空")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        return card

    def _build_action_card(self) -> SectionCard:
        card = SectionCard("保存")
        self._save_button = QPushButton("保存并应用")
        self._save_button.clicked.connect(lambda: self.save_requested.emit(self.current_config()))
        card.body_layout.addWidget(self._save_button)
        self._status = StatusLabel("等待加载配置。")
        card.body_layout.addWidget(self._status)
        self._controls.append(self._save_button)
        return card

    def _add_text_field(self, card: SectionCard, label: str, placeholder: str) -> QLineEdit:
        card.body_layout.addWidget(self._label(label))
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        card.body_layout.addWidget(line_edit)
        self._controls.append(line_edit)
        return line_edit

    def _set_markers(self, markers: tuple[str, ...]) -> None:
        self._markers.clear()
        for marker in markers:
            self._markers.addItem(marker)
        self._update_marker_list_height()

    def _read_markers(self) -> list[str]:
        markers: list[str] = []
        for index in range(self._markers.count()):
            marker = self._markers.item(index).text().strip()
            if marker and marker not in markers:
                markers.append(marker)
        return markers

    def _update_marker_list_height(self) -> None:
        visible_rows = min(max(self._markers.count(), 1), 6)
        row_heights = [
            self._markers.sizeHintForRow(index)
            for index in range(self._markers.count())
        ]
        row_height = max([height for height in row_heights if height > 0] or [32])
        frame_height = 2 * self._markers.frameWidth() + 8
        self._markers.setFixedHeight(max(42, visible_rows * row_height + frame_height))

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    @staticmethod
    def _read_text(line_edit: QLineEdit) -> str:
        return line_edit.text().strip()

    @staticmethod
    def _display_working_path(path: Path | None) -> str:
        if path is None:
            return ""
        expanded = path.expanduser()
        if not expanded.is_absolute():
            return expanded.as_posix()
        try:
            return expanded.resolve(strict=False).relative_to(Path.cwd()).as_posix()
        except ValueError:
            return str(expanded.resolve(strict=False))

    @classmethod
    def _read_path(cls, line_edit: QLineEdit) -> Path | None:
        text = cls._read_text(line_edit)
        return Path(text) if text else None