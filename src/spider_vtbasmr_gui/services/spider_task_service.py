from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from spider_vtbasmr import BatchCrawlResult, CrawlMode, PageOrder, VtbCrawler, VtbCrawlSummary
from spider_vtbasmr.manager.login_state_manager import LoginStateManager
from spider_vtbasmr_gui.services.runtime_context import RuntimeContext, RuntimeContextProvider


@dataclass(frozen=True, slots=True)
class VtbTagOption:
    tag_name: str
    display_name: str


@dataclass(frozen=True, slots=True)
class LoginTaskResult:
    final_url: str
    summary_text: str


@dataclass(frozen=True, slots=True)
class CrawlTaskResult:
    crawl_summaries: list[VtbCrawlSummary]
    failed_tag_names: list[str]
    log_file_path: str
    summary_text: str


class SpiderTaskService:
    def __init__(
        self,
        context_provider: RuntimeContextProvider,
        *,
        crawler_factory: Callable[[RuntimeContext], VtbCrawler] | None = None,
    ) -> None:
        self._context_provider = context_provider
        self._crawler_factory = crawler_factory or self._build_crawler

    def load_vtb_tag_options(self) -> list[VtbTagOption]:
        context = self._context_provider.require()
        payload = json.loads(context.vtb_config.config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("VTB 配置必须是 JSON object")
        return [
            VtbTagOption(
                tag_name=str(tag_name),
                display_name=str(raw_config.get("name") or tag_name),
            )
            for tag_name, raw_config in payload.items()
            if isinstance(raw_config, dict)
        ]

    def run_login(self) -> LoginTaskResult:
        context = self._context_provider.require()
        result = LoginStateManager(config_manager=context.spider_config).create_login_state(
            is_headless=False,
        )
        return LoginTaskResult(
            final_url=result.final_url,
            summary_text="登录完成，状态已更新。",
        )

    def run_crawl(
        self,
        tag_names: list[str],
        crawl_mode: CrawlMode,
        page_order: PageOrder,
        log_file_name: str | None = None,
    ) -> CrawlTaskResult:
        if not tag_names:
            raise ValueError("请至少选择一个 Tag")
        context = self._context_provider.require()
        result = self._crawler_factory(context).crawl_vtb_list(
            tag_names=tag_names,
            crawl_mode=CrawlMode(crawl_mode),
            page_order=PageOrder(page_order),
            log_file_name=log_file_name.strip() if log_file_name and log_file_name.strip() else None,
            is_headless=True,
        )
        return self._result(result)

    @staticmethod
    def _build_crawler(context: RuntimeContext) -> VtbCrawler:
        return VtbCrawler(
            config_manager=context.spider_config,
            vtb_config_manager=context.vtb_config,
        )

    @staticmethod
    def _result(result: BatchCrawlResult) -> CrawlTaskResult:
        success_count = len(result.crawl_summaries)
        failed_count = len(result.failed_tag_names)
        return CrawlTaskResult(
            crawl_summaries=result.crawl_summaries,
            failed_tag_names=result.failed_tag_names,
            log_file_path=result.log_file_path,
            summary_text=(
                f"抓取完成：成功 {success_count} 项，失败 {failed_count} 项。"
                f" 日志：{result.log_file_path}"
            ),
        )