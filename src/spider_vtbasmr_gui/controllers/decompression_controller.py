from __future__ import annotations

from PySide6.QtCore import QObject

from spider_vtbasmr_gui.controllers.task_coordinator import TaskCoordinator
from spider_vtbasmr_gui.services.decompression_service import (
    DecompressionPreviewResult,
    DecompressionResult,
    DecompressionService,
)
from spider_vtbasmr_gui.ui.pages.resource_decompression_page import (
    DecompressionRequest,
    ResourceDecompressionPage,
)


class DecompressionController(QObject):
    def __init__(
        self,
        page: ResourceDecompressionPage,
        service: DecompressionService,
        tasks: TaskCoordinator,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._page = page
        self._service = service
        self._tasks = tasks
        page.preview_requested.connect(self.preview)
        page.decompress_requested.connect(self.decompress)

    def refresh(self) -> None:
        self._page.set_files([])
        self._page.show_status("请选择源目录和目标目录。")

    def preview(self, request: DecompressionRequest) -> None:
        if not self._valid(request):
            return
        self._page.show_status("正在扫描压缩文件…", "warning")
        self._tasks.run(
            lambda: self._service.preview(request.source_root, request.target_root),
            busy_message="正在扫描压缩文件…",
            on_success=self._preview_succeeded,
            on_error=lambda error: self._page.show_status(error, "error"),
        )

    def decompress(self, request: DecompressionRequest) -> None:
        if not self._valid(request):
            return
        self._page.show_status("正在后台解压…", "warning")
        self._tasks.run(
            lambda: self._service.decompress(
                request.source_root,
                request.target_root,
                request.password,
            ),
            busy_message="正在解压资源…",
            on_success=self._decompress_succeeded,
            on_error=lambda error: self._page.show_status(error, "error"),
        )

    def _valid(self, request: DecompressionRequest) -> bool:
        if not request.source_root or not request.target_root:
            self._page.show_status("请同时选择源目录和目标目录。", "error")
            return False
        return True

    def _preview_succeeded(self, result: object) -> None:
        assert isinstance(result, DecompressionPreviewResult)
        self._page.set_files(result.files)
        self._page.show_status(result.summary_text, "success")

    def _decompress_succeeded(self, result: object) -> None:
        assert isinstance(result, DecompressionResult)
        self._page.show_status(result.summary_text, "success")