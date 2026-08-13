from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from spider_vtbasmr_gui.controllers.task_coordinator import TaskCoordinator
from spider_vtbasmr_gui.services.spider_task_service import (
    CrawlTaskResult,
    LoginTaskResult,
    SpiderTaskService,
)
from spider_vtbasmr_gui.ui.pages.crawl_page import CrawlPage, CrawlRequest


class CrawlController(QObject):
    crawl_progress_changed = Signal(str, int, int)

    def __init__(
        self,
        page: CrawlPage,
        service: SpiderTaskService,
        tasks: TaskCoordinator,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._page = page
        self._service = service
        self._tasks = tasks
        self.crawl_progress_changed.connect(page.show_crawl_progress)
        page.login_requested.connect(self.login)
        page.crawl_requested.connect(self.crawl)

    def refresh(self) -> None:
        try:
            options = self._service.load_vtb_tag_options()
        except Exception as error:
            self._page.set_tag_options([])
            self._page.show_list_status(f"VTB 列表不可用：{error}", "warning")
            return
        self._page.set_tag_options(options)
        self._page.show_list_status(f"已加载 {len(options)} 个 VTB。", "success")

    def login(self) -> None:
        self._page.show_login_status("正在打开登录窗口…", "warning")
        self._tasks.run(
            self._service.run_login,
            busy_message="正在创建登录状态…",
            on_success=self._login_succeeded,
            on_error=lambda error: self._page.show_login_status(error, "error"),
        )

    def crawl(self, request: CrawlRequest) -> None:
        if not request.tag_names:
            self._page.show_crawl_status("请至少选择一个 VTB。", "error")
            return
        self._page.show_crawl_progress("等待开始", 0, len(request.tag_names))
        self._page.show_crawl_status("抓取任务正在后台运行…", "warning")
        self._tasks.run(
            lambda: self._service.run_crawl(
                request.tag_names,
                request.crawl_mode,
                request.page_order,
                request.log_file_name,
                on_progress=self.crawl_progress_changed.emit,
            ),
            busy_message="正在抓取数据…",
            on_success=self._crawl_succeeded,
            on_error=lambda error: self._page.show_crawl_status(error, "error"),
        )

    def _login_succeeded(self, result: object) -> None:
        assert isinstance(result, LoginTaskResult)
        self._page.show_login_status(result.summary_text, "success")

    def _crawl_succeeded(self, result: object) -> None:
        assert isinstance(result, CrawlTaskResult)
        tone = "warning" if result.failed_tag_names else "success"
        self._page.show_crawl_status(result.summary_text, tone)