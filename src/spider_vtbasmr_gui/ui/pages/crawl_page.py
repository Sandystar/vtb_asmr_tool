from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from spider_vtbasmr import CrawlMode, PageOrder
from spider_vtbasmr_gui.services.spider_task_service import VtbTagOption
from spider_vtbasmr_gui.ui.widgets import SectionCard, StatusLabel


@dataclass(frozen=True, slots=True)
class CrawlRequest:
    tag_names: list[str]
    crawl_mode: CrawlMode
    page_order: PageOrder
    log_file_name: str | None


class CrawlPage(QWidget):
    login_requested = Signal()
    crawl_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        self._build()

    def set_tag_options(self, options: list[VtbTagOption]) -> None:
        self._tag_list.clear()
        for option in options:
            item = QListWidgetItem(option.display_name)
            item.setData(Qt.ItemDataRole.UserRole, option.tag_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._tag_list.addItem(item)
        self._update_count()

    def set_busy(self, busy: bool) -> None:
        for control in self._controls:
            control.setDisabled(busy)

    def show_login_status(self, message: str, tone: str = "default") -> None:
        self._login_status.show_status(message, tone)

    def show_crawl_status(self, message: str, tone: str = "default") -> None:
        self._crawl_status.show_status(message, tone)

    def show_list_status(self, message: str, tone: str = "default") -> None:
        self._list_status.show_status(message, tone)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        columns = QWidget()
        columns.setObjectName("contentPanel")
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(16)

        action_card = SectionCard("任务参数")
        self._login_button = QPushButton("打开登录窗口")
        self._login_button.clicked.connect(self.login_requested.emit)
        action_card.body_layout.addWidget(self._login_button)
        self._login_status = StatusLabel("等待登录。")
        action_card.body_layout.addWidget(self._login_status)
        action_card.body_layout.addWidget(self._label("抓取模式"))
        self._mode = QComboBox()
        self._mode.addItem("抓到已归档即停止", CrawlMode.UNTIL_ARCHIVED)
        self._mode.addItem("跳过已归档", CrawlMode.SKIP_ARCHIVED)
        self._mode.addItem("全部抓取", CrawlMode.ALL)
        action_card.body_layout.addWidget(self._mode)
        action_card.body_layout.addWidget(self._label("页面顺序"))
        self._order = QComboBox()
        self._order.addItem("页码递增", PageOrder.ASCENDING)
        self._order.addItem("页码递减", PageOrder.DESCENDING)
        action_card.body_layout.addWidget(self._order)
        action_card.body_layout.addWidget(self._label("日志名称（可选）"))
        self._log_name = QLineEdit()
        action_card.body_layout.addWidget(self._log_name)
        self._crawl_button = QPushButton("开始后台抓取")
        self._crawl_button.clicked.connect(self._emit_crawl)
        action_card.body_layout.addWidget(self._crawl_button)
        self._crawl_status = StatusLabel("等待抓取。")
        action_card.body_layout.addWidget(self._crawl_status)
        action_card.body_layout.addStretch(1)
        columns_layout.addWidget(action_card, 4)

        list_card = SectionCard("VTB 列表")
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        select_all = QPushButton("全选")
        clear_all = QPushButton("清空")
        select_all.setObjectName("secondaryButton")
        clear_all.setObjectName("secondaryButton")
        select_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        clear_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        self._count = QLabel("已选 0 / 0")
        self._count.setObjectName("countLabel")
        toolbar_layout.addWidget(select_all)
        toolbar_layout.addWidget(clear_all)
        toolbar_layout.addWidget(self._count)
        toolbar_layout.addStretch(1)
        list_card.body_layout.addWidget(toolbar)
        self._tag_list = QListWidget()
        self._tag_list.itemChanged.connect(self._update_count)
        list_card.body_layout.addWidget(self._tag_list, 1)
        self._list_status = StatusLabel("等待加载 VTB 配置。")
        list_card.body_layout.addWidget(self._list_status)
        columns_layout.addWidget(list_card, 5)
        layout.addWidget(columns, 1)
        self._controls = [
            self._login_button,
            self._mode,
            self._order,
            self._log_name,
            self._crawl_button,
            self._tag_list,
            select_all,
            clear_all,
        ]

    def _emit_crawl(self) -> None:
        self.crawl_requested.emit(
            CrawlRequest(
                tag_names=self.selected_tag_names(),
                crawl_mode=self._mode.currentData(),
                page_order=self._order.currentData(),
                log_file_name=self._log_name.text().strip() or None,
            )
        )

    def selected_tag_names(self) -> list[str]:
        return [
            str(self._tag_list.item(index).data(Qt.ItemDataRole.UserRole))
            for index in range(self._tag_list.count())
            if self._tag_list.item(index).checkState() == Qt.CheckState.Checked
        ]

    def _set_all(self, state: Qt.CheckState) -> None:
        for index in range(self._tag_list.count()):
            self._tag_list.item(index).setCheckState(state)

    def _update_count(self) -> None:
        self._count.setText(f"已选 {len(self.selected_tag_names())} / {self._tag_list.count()}")

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label