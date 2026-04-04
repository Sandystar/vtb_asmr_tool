from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager
from spider_vtbasmr.manager.vtb_crawl_manager import CrawlMode, VtbCrawlManager, VtbCrawlSummary


@dataclass(slots=True)
class BatchCrawlResult:
    crawl_summaries: list[VtbCrawlSummary]
    failed_tag_names: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "crawl_summaries": [crawl_summary.to_dict() for crawl_summary in self.crawl_summaries],
            "failed_tag_names": self.failed_tag_names,
        }


class BatchUntilArchivedCrawler:
    def __init__(
        self,
        vtb_config_manager: VtbConfigManager | None = None,
        vtb_crawl_manager: VtbCrawlManager | None = None,
    ) -> None:
        self._vtb_config_manager = vtb_config_manager or VtbConfigManager()
        self._vtb_crawl_manager = vtb_crawl_manager or VtbCrawlManager()

    def crawl_all_vtb_configs(
        self,
        *,
        is_headless: bool = True,
        timeout_milliseconds: int = 60000,
    ) -> BatchCrawlResult:
        crawl_summaries: list[VtbCrawlSummary] = []
        failed_tag_names: list[str] = []

        for vtb_config in self._vtb_config_manager.get_all_vtb_configs():
            self._delete_log_file(vtb_config.log_file_path)
            print(f"[batch] start tag={vtb_config.name}", flush=True)
            try:
                crawl_summary = self._vtb_crawl_manager.crawl_vtb(
                    tag_name=vtb_config.name,
                    crawl_mode=CrawlMode.UNTIL_ARCHIVED,
                    is_headless=is_headless,
                    timeout_milliseconds=timeout_milliseconds,
                )
            except Exception as error:
                failed_tag_names.append(vtb_config.name)
                print(f"[batch] failed tag={vtb_config.name} error={error}", flush=True)
                continue

            crawl_summaries.append(crawl_summary)
            print(
                f"[batch] completed tag={vtb_config.name} stopped_reason={crawl_summary.stopped_reason}",
                flush=True,
            )

        return BatchCrawlResult(
            crawl_summaries=crawl_summaries,
            failed_tag_names=failed_tag_names,
        )

    def _delete_log_file(self, log_file_path: Path) -> None:
        if not log_file_path.exists():
            return
        log_file_path.unlink()
        print(f"[batch] deleted log_file={log_file_path}", flush=True)
