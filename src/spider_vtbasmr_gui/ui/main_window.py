from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
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
    _PAGE_META = (
        ("登陆抓取", "选择目标和策略，启动一次可追踪的后台抓取任务。"),
        ("资源转存", "从抓取日志提取分享资源，并提交到 NAS 下载。"),
        ("资源解压", "扫描本地归档，预览并按内容整理输出。"),
        ("数据配置", ""),
    )

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

    def switch_page(self, page_index: int) -> None:
        if not 0 <= page_index < self._pages.count():
            return
        self._pages.setCurrentIndex(page_index)
        self._navigation_buttons[page_index].setChecked(True)
        self._update_page_header(page_index)

    def _build(self) -> None:
        self.setWindowTitle("VTB ASMR · 工作台")
        self.setMinimumSize(1080, 720)
        self.resize(1280, 860)

        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_workspace(), 1)
        self.switch_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebarRail")
        sidebar.setFixedWidth(228)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 16, 18)
        sidebar_layout.setSpacing(0)

        brand = QWidget()
        brand.setObjectName("sidebarBrand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(4)
        name = QLabel("VTB ASMR")
        name.setObjectName("brandName")
        descriptor = QLabel("COLLECTOR WORKSPACE")
        descriptor.setObjectName("brandDescriptor")
        brand_layout.addWidget(name)
        brand_layout.addWidget(descriptor)
        sidebar_layout.addWidget(brand)
        sidebar_layout.addSpacing(38)

        button_group = QButtonGroup(self)
        button_group.setExclusive(True)
        for index, (title, _) in enumerate(self._PAGE_META):
            button = QPushButton(title)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=index: self.switch_page(page))
            button_group.addButton(button)
            sidebar_layout.addWidget(button)
            self._navigation_buttons.append(button)
            if index != len(self._PAGE_META) - 1:
                sidebar_layout.addSpacing(4)

        sidebar_layout.addStretch(1)
        return sidebar

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        workspace.setObjectName("workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(42, 30, 42, 26)
        workspace_layout.setSpacing(24)

        header = QWidget()
        header.setObjectName("mainHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(18)

        header_copy = QWidget()
        copy_layout = QVBoxLayout(header_copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(5)
        self._page_title = QLabel()
        self._page_title.setObjectName("pageTitle")
        self._page_description = QLabel()
        self._page_description.setObjectName("pageDescription")
        self._page_description.setWordWrap(True)
        copy_layout.addWidget(self._page_title)
        copy_layout.addWidget(self._page_description)
        header_layout.addWidget(header_copy, 1)
        workspace_layout.addWidget(header)

        page_surface = QWidget()
        page_surface.setObjectName("pageSurface")
        page_layout = QVBoxLayout(page_surface)
        page_layout.setContentsMargins(0, 0, 0, 0)
        self._pages = QStackedWidget()
        self._pages.setObjectName("pageStack")
        page_layout.addWidget(self._pages)
        workspace_layout.addWidget(page_surface, 1)

        self._crawl_page = CrawlPage()
        self._resource_transfer_page = ResourceTransferPage()
        self._resource_decompression_page = ResourceDecompressionPage()
        self._basic_config_page = BasicConfigPage()
        for page in (
            self._crawl_page,
            self._resource_transfer_page,
            self._resource_decompression_page,
            self._basic_config_page,
        ):
            self._pages.addWidget(page)
        return workspace

    def _update_page_header(self, page_index: int) -> None:
        title, description = self._PAGE_META[page_index]
        self._page_title.setText(title)
        self._page_description.setText(description)
        self._page_description.setVisible(bool(description))
