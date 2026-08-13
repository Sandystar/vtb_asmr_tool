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
    QProgressBar,
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

    def show_crawl_progress(self, name: str, current_count: int, total_count: int) -> None:
        resolved_total = max(0, total_count)
        resolved_current = min(max(0, current_count), resolved_total)
        self._progress_name.setText(name or "等待任务")
        self._progress_current.setText(str(resolved_current))
        self._progress_total.setText(str(resolved_total))
        self._progress_bar.setRange(0, resolved_total or 1)
        self._progress_bar.setValue(resolved_current)
        self._progress_bar.setFormat(
            f"{resolved_current} / {resolved_total}" if resolved_total else "等待任务"
        )

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        progress_card = SectionCard("抓取进度")
        progress_metrics = QWidget()
        progress_metrics.setObjectName("progressMetrics")
        progress_metrics_layout = QHBoxLayout(progress_metrics)
        progress_metrics_layout.setContentsMargins(0, 0, 0, 0)
        progress_metrics_layout.setSpacing(24)
        self._progress_name = self._add_progress_metric(
            progress_metrics_layout,
            "当前抓取",
            "等待任务",
            stretch=1,
        )
        self._progress_current = self._add_progress_metric(
            progress_metrics_layout,
            "当前个数",
            "0",
        )
        self._progress_total = self._add_progress_metric(
            progress_metrics_layout,
            "总个数",
            "0",
        )
        progress_card.body_layout.addWidget(progress_metrics)
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("crawlProgressBar")
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("等待任务")
        self._progress_bar.setTextVisible(True)
        progress_card.body_layout.addWidget(self._progress_bar)
        layout.addWidget(progress_card)

        login_card = SectionCard("更新状态")
        login_row = QWidget()
        login_row.setObjectName("fieldRow")
        login_row_layout = QHBoxLayout(login_row)
        login_row_layout.setContentsMargins(0, 0, 0, 0)
        login_row_layout.setSpacing(16)
        self._login_button = QPushButton("登录并保存状态")
        self._login_button.clicked.connect(self.login_requested.emit)
        self._login_status = StatusLabel("没过期可以不用执行。")
        login_row_layout.addWidget(self._login_button)
        login_row_layout.addWidget(self._login_status, 1)
        login_card.body_layout.addWidget(login_row)
        layout.addWidget(login_card)

        task_card = SectionCard("任务设置")
        task_columns = QWidget()
        task_columns.setObjectName("contentPanel")
        task_columns_layout = QHBoxLayout(task_columns)
        task_columns_layout.setContentsMargins(0, 0, 0, 0)
        task_columns_layout.setSpacing(20)

        parameters = QWidget()
        parameters.setObjectName("taskParameters")
        parameters_layout = QVBoxLayout(parameters)
        parameters_layout.setContentsMargins(0, 0, 0, 0)
        parameters_layout.setSpacing(10)
        parameters_layout.addWidget(self._label("抓取模式"))
        self._mode = QComboBox()
        self._mode.addItem("抓到已归档即停止", CrawlMode.UNTIL_ARCHIVED)
        self._mode.addItem("跳过已归档", CrawlMode.SKIP_ARCHIVED)
        self._mode.addItem("全部抓取", CrawlMode.ALL)
        parameters_layout.addWidget(self._mode)
        parameters_layout.addWidget(self._label("页面顺序"))
        self._order = QComboBox()
        self._order.addItem("页码递增", PageOrder.ASCENDING)
        self._order.addItem("页码递减", PageOrder.DESCENDING)
        parameters_layout.addWidget(self._order)
        parameters_layout.addWidget(self._label("日志名称（可选）"))
        self._log_name = QLineEdit()
        parameters_layout.addWidget(self._log_name)
        self._crawl_button = QPushButton("开始后台抓取")
        self._crawl_button.clicked.connect(self._emit_crawl)
        parameters_layout.addWidget(self._crawl_button)
        self._crawl_status = StatusLabel("等待抓取。")
        parameters_layout.addWidget(self._crawl_status)
        parameters_layout.addStretch(1)
        task_columns_layout.addWidget(parameters, 4)

        vtb_list = QWidget()
        vtb_list.setObjectName("vtbSelection")
        vtb_list_layout = QVBoxLayout(vtb_list)
        vtb_list_layout.setContentsMargins(0, 0, 0, 0)
        vtb_list_layout.setSpacing(10)
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
        vtb_list_layout.addWidget(toolbar)
        self._tag_list = QListWidget()
        self._tag_list.itemChanged.connect(self._update_count)
        vtb_list_layout.addWidget(self._tag_list, 1)
        self._list_status = StatusLabel("等待加载 VTB 配置。")
        vtb_list_layout.addWidget(self._list_status)
        task_columns_layout.addWidget(vtb_list, 5)

        task_card.body_layout.addWidget(task_columns, 1)
        layout.addWidget(task_card, 1)
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
    def _add_progress_metric(
        layout: QHBoxLayout,
        title: str,
        value: str,
        *,
        stretch: int = 0,
    ) -> QLabel:
        metric = QWidget()
        metric.setObjectName("progressMetric")
        metric_layout = QVBoxLayout(metric)
        metric_layout.setContentsMargins(0, 0, 0, 0)
        metric_layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("progressMetricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("progressMetricValue")
        metric_layout.addWidget(title_label)
        metric_layout.addWidget(value_label)
        layout.addWidget(metric, stretch)
        return value_label

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label