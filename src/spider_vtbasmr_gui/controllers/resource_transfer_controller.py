from __future__ import annotations

from PySide6.QtCore import QObject

from spider_vtbasmr_gui.controllers.task_coordinator import TaskCoordinator
from spider_vtbasmr_gui.services.resource_transfer_service import (
    ParsedResourceLogResult,
    ResourceTransferResult,
    ResourceTransferService,
)
from spider_vtbasmr_gui.ui.pages.resource_transfer_page import ResourceTransferPage


class ResourceTransferController(QObject):
    def __init__(
        self,
        page: ResourceTransferPage,
        service: ResourceTransferService,
        tasks: TaskCoordinator,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._page = page
        self._service = service
        self._tasks = tasks
        page.login_requested.connect(self.login)
        page.parse_requested.connect(self.parse)
        page.transfer_requested.connect(self.transfer)

    def refresh(self) -> None:
        try:
            path = self._service.default_log_directory()
        except Exception as error:
            self._page.show_parse_status(f"日志目录不可用：{error}", "warning")
            return
        self._page.set_default_log_directory(path)
        self._page.show_parse_status("请选择抓取日志。")

    def login(self) -> None:
        self._page.show_login_status(
            "正在打开独立浏览器。请先完成 FNOS 登录；进入百度网盘后，"
            "请手动勾选用户协议和隐私协议，再点击“授权登录”。",
            "warning",
        )
        self._tasks.run(
            self._service.capture_fnos_auth,
            busy_message="正在登录 FNOS…",
            on_success=lambda result: self._page.show_login_status(str(result), "success"),
            on_error=lambda error: self._page.show_login_status(error, "error"),
        )

    def parse(self, log_file_path: str) -> None:
        if not log_file_path:
            self._page.show_parse_status("请先选择日志文件。", "error")
            return
        self._page.show_parse_status("正在解析日志…", "warning")
        self._tasks.run(
            lambda: self._service.parse_log_file(log_file_path),
            busy_message="正在解析抓取日志…",
            on_success=self._parse_succeeded,
            on_error=lambda error: self._page.show_parse_status(error, "error"),
        )

    def transfer(self) -> None:
        items = self._page.resource_items
        self._page.show_transfer_status("正在转存并提交 NAS 下载…", "warning")
        self._tasks.run(
            lambda: self._service.transfer_resources(items),
            busy_message="正在处理网盘资源…",
            on_success=self._transfer_succeeded,
            on_error=lambda error: self._page.show_transfer_status(error, "error"),
        )

    def _parse_succeeded(self, result: object) -> None:
        assert isinstance(result, ParsedResourceLogResult)
        self._page.set_log_file_path(result.log_file_path)
        self._page.set_resource_items(result.resource_items)
        self._page.show_parse_status(result.summary_text, "success")

    def _transfer_succeeded(self, result: object) -> None:
        assert isinstance(result, ResourceTransferResult)
        self._page.show_transfer_status(result.summary_text, "success")