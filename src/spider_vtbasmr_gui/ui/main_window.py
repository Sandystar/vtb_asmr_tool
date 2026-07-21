from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from spider_vtbasmr_gui.ui.pages import (
    BasicConfigPage,
    CrawlPage,
    ResourceDecompressionPage,
    ResourceTransferPage,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._navigation_buttons: list[QPushButton] = []
        self._build()

    @property
    def basic_config_page(self) -> BasicConfigPage:
        return self._basic_config_page

    @property
    def crawl_page(self) -> CrawlPage:
        return self._crawl_page

    @property
    def resource_transfer_page(self) -> ResourceTransferPage:
        return self._resource_transfer_page

    @property
    def resource_decompression_page(self) -> ResourceDecompressionPage:
        return self._resource_decompression_page

    @property
    def current_page_index(self) -> int:
        return self._pages.currentIndex()

    def set_busy(self, busy: bool, message: str) -> None:
        for button in self._navigation_buttons:
            button.setDisabled(busy)
        self._basic_config_page.set_busy(busy)
        self._crawl_page.set_busy(busy)
        self._resource_transfer_page.set_busy(busy)
        self._resource_decompression_page.set_busy(busy)
        self.statusBar().showMessage(message)

    def switch_page(self, page_index: int) -> None:
        self._pages.setCurrentIndex(page_index)

    def _build(self) -> None:
        self.setWindowTitle("VTB ASMR 工具")
        self.setMinimumSize(1080, 720)
        self.resize(1280, 860)

        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("VTB ASMR 工具")
        title.setObjectName("appTitle")
        subtitle = QLabel("登录、抓取、网盘转存与本地解压，运行数据统一保存在工程内 .data。")
        subtitle.setObjectName("appSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        navigation = QWidget()
        navigation.setObjectName("transparentPanel")
        navigation_layout = QHBoxLayout(navigation)
        navigation_layout.setContentsMargins(0, 2, 0, 2)
        navigation_layout.setSpacing(8)
        button_group = QButtonGroup(self)
        button_group.setExclusive(True)
        for index, text in enumerate(("基本配置", "登录与抓取", "资源转存", "资源解压")):
            button = QPushButton(text)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=index: self.switch_page(page))
            button_group.addButton(button)
            navigation_layout.addWidget(button)
            self._navigation_buttons.append(button)
        navigation_layout.addStretch(1)
        self._navigation_buttons[0].setChecked(True)
        layout.addWidget(navigation)

        container = QWidget()
        container.setObjectName("pageContainer")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(18, 18, 18, 18)
        self._pages = QStackedWidget()
        container_layout.addWidget(self._pages)
        layout.addWidget(container, 1)

        self._basic_config_page = BasicConfigPage()
        self._crawl_page = CrawlPage()
        self._resource_transfer_page = ResourceTransferPage()
        self._resource_decompression_page = ResourceDecompressionPage()
        for page in (
            self._basic_config_page,
            self._crawl_page,
            self._resource_transfer_page,
            self._resource_decompression_page,
        ):
            self._pages.addWidget(page)

        status_bar = QStatusBar()
        status_bar.showMessage("正在加载本地配置…")
        self.setStatusBar(status_bar)