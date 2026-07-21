from __future__ import annotations

from PySide6.QtCore import QObject

from spider_vtbasmr_gui.config import AppConfigManager
from spider_vtbasmr_gui.controllers.config_controller import ConfigController
from spider_vtbasmr_gui.controllers.crawl_controller import CrawlController
from spider_vtbasmr_gui.controllers.decompression_controller import DecompressionController
from spider_vtbasmr_gui.controllers.resource_transfer_controller import ResourceTransferController
from spider_vtbasmr_gui.controllers.task_coordinator import TaskCoordinator
from spider_vtbasmr_gui.services import (
    DecompressionService,
    ResourceTransferService,
    RuntimeContextProvider,
    SpiderTaskService,
)
from spider_vtbasmr_gui.ui.main_window import MainWindow
from spider_vtbasmr_gui.ui.task_runner import TaskRunner


class ApplicationController(QObject):
    def __init__(
        self,
        window: MainWindow,
        config_manager: AppConfigManager,
        context_provider: RuntimeContextProvider,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent or window)
        task_runner = TaskRunner(self)
        self._tasks = TaskCoordinator(task_runner, self)
        self._tasks.busy_changed.connect(window.set_busy)

        self._config = ConfigController(
            window.basic_config_page,
            config_manager,
            context_provider,
            self,
        )
        self._crawl = CrawlController(
            window.crawl_page,
            SpiderTaskService(context_provider),
            self._tasks,
            self,
        )
        self._transfer = ResourceTransferController(
            window.resource_transfer_page,
            ResourceTransferService(context_provider),
            self._tasks,
            self,
        )
        self._decompression = DecompressionController(
            window.resource_decompression_page,
            DecompressionService(context_provider),
            self._tasks,
            self,
        )
        self._config.config_applied.connect(lambda _: self.refresh_runtime_pages())

    def start(self) -> None:
        self._config.load()

    def refresh_runtime_pages(self) -> None:
        self._crawl.refresh()
        self._transfer.refresh()
        self._decompression.refresh()