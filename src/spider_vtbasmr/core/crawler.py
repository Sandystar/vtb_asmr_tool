from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

from spider_vtbasmr.browser.playwright_browser_client import PlaywrightBrowserClient
from spider_vtbasmr.manager.archive_manager import ArchiveManager
from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.log_manager import LogManager, LogRecord
from spider_vtbasmr.manager.save_manager import SaveManager
from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager
from spider_vtbasmr.scraper.detail_page_scraper import DetailPageResult, DetailPageScraper
from spider_vtbasmr.scraper.page_access import AuthenticationRequiredError
from spider_vtbasmr.scraper.tag_page_scraper import CoverItem, TagPageResult, TagPageScraper


class CrawlMode(str, Enum):
    ALL = "all"
    SKIP_ARCHIVED = "skip_archived"
    UNTIL_ARCHIVED = "until_archived"


class PageOrder(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


@dataclass(slots=True)
class VtbCrawlSummary:
    tag_name: str
    crawl_mode: str
    page_order: str
    processed_page_count: int
    processed_cover_count: int
    saved_detail_count: int
    skipped_archived_count: int
    archive_added_count: int
    stopped_reason: str
    log_file_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "tag_name": self.tag_name,
            "crawl_mode": self.crawl_mode,
            "page_order": self.page_order,
            "processed_page_count": self.processed_page_count,
            "processed_cover_count": self.processed_cover_count,
            "saved_detail_count": self.saved_detail_count,
            "skipped_archived_count": self.skipped_archived_count,
            "archive_added_count": self.archive_added_count,
            "stopped_reason": self.stopped_reason,
            "log_file_path": self.log_file_path,
        }


@dataclass(slots=True)
class BatchCrawlResult:
    crawl_summaries: list[VtbCrawlSummary]
    failed_tag_names: list[str]
    log_file_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "crawl_summaries": [crawl_summary.to_dict() for crawl_summary in self.crawl_summaries],
            "failed_tag_names": self.failed_tag_names,
            "log_file_path": self.log_file_path,
        }


class VtbCrawler:
    def __init__(
        self,
        vtb_config_manager: VtbConfigManager | None = None,
        tag_page_scraper: TagPageScraper | None = None,
        detail_page_scraper: DetailPageScraper | None = None,
        browser_client: PlaywrightBrowserClient | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self._vtb_config_manager = vtb_config_manager or VtbConfigManager()
        self._config_manager = config_manager or ConfigManager()
        self._browser_client = browser_client or PlaywrightBrowserClient(
            config_manager=self._config_manager,
        )
        self._tag_page_scraper = tag_page_scraper or TagPageScraper(
            browser_client=self._browser_client,
            config_manager=self._config_manager,
        )
        self._detail_page_scraper = detail_page_scraper or DetailPageScraper(
            browser_client=self._browser_client,
            config_manager=self._config_manager,
        )

    def crawl_single_vtb(
        self,
        tag_name: str,
        *,
        crawl_mode: CrawlMode = CrawlMode.SKIP_ARCHIVED,
        page_order: PageOrder = PageOrder.ASCENDING,
        log_file_name: str | None = None,
        is_headless: bool = True,
        timeout_milliseconds: int = 60000,
    ) -> VtbCrawlSummary:
        vtb_config = self._vtb_config_manager.get_vtb_config(tag_name)
        archive_manager = ArchiveManager(vtb_config.archive_file_path)
        save_manager = SaveManager(vtb_config.save_dir_path)
        login_state = self._config_manager.get_storage_state()
        log_manager = LogManager(
            log_file_name=log_file_name,
            config_manager=self._config_manager,
        )

        self._print_progress(
            tag_name=vtb_config.name,
            message=(
                f"prepare crawl_mode={crawl_mode.value} page_order={page_order.value} "
                f"first_page={vtb_config.url}"
            ),
        )
        browser_session = self._browser_client.open_logged_in_browser_session(
            storage_state=login_state or {},
            is_headless=is_headless,
        )

        processed_page_count = 0
        processed_cover_count = 0
        saved_detail_count = 0
        skipped_archived_count = 0
        archive_added_count = 0
        stopped_reason = "completed"

        try:
            first_tag_page_result = self._tag_page_scraper.scrape_tag_page(
                page_url=vtb_config.url,
                is_headless=is_headless,
                timeout_milliseconds=timeout_milliseconds,
                browser_session=browser_session,
            )
            page_results_by_url = {first_tag_page_result.page_url: first_tag_page_result}
            page_urls = self._resolve_page_urls(
                first_tag_page_result=first_tag_page_result,
                page_order=page_order,
            )

            self._print_progress(
                tag_name=vtb_config.name,
                message=(
                    f"start crawl_mode={crawl_mode.value} page_order={page_order.value} "
                    f"page_count={len(page_urls)}"
                ),
            )

            for page_index, page_url in enumerate(page_urls, start=1):
                current_tag_page_result = page_results_by_url.get(page_url)
                if current_tag_page_result is None:
                    current_tag_page_result = self._tag_page_scraper.scrape_tag_page(
                        page_url=page_url,
                        is_headless=is_headless,
                        timeout_milliseconds=timeout_milliseconds,
                        browser_session=browser_session,
                    )
                    page_results_by_url[current_tag_page_result.page_url] = current_tag_page_result

                processed_page_count += 1
                self._print_progress(
                    tag_name=vtb_config.name,
                    message=(
                        f"page {page_index}/{len(page_urls)} fetched: {current_tag_page_result.page_url} "
                        f"cover_count={len(current_tag_page_result.cover_items)}"
                    ),
                )

                should_stop_crawl = False
                for cover_index, cover_item in enumerate(current_tag_page_result.cover_items, start=1):
                    processed_cover_count += 1
                    archive_item_id = self._get_archive_item_id(cover_item)
                    archive_match_value = self._get_archive_match_value(cover_item)
                    is_archived = self._is_cover_item_archived(
                        archive_manager=archive_manager,
                        archive_item_id=archive_item_id,
                        archive_match_value=archive_match_value,
                    )

                    if crawl_mode == CrawlMode.SKIP_ARCHIVED and is_archived:
                        skipped_archived_count += 1
                        self._print_progress(
                            tag_name=vtb_config.name,
                            message=(
                                f"skip archived page={page_index} cover={cover_index} "
                                f"post_id={cover_item.post_id or '-'} archive_key={archive_item_id}"
                            ),
                        )
                        continue

                    if crawl_mode == CrawlMode.UNTIL_ARCHIVED and is_archived:
                        skipped_archived_count += 1
                        stopped_reason = "stopped_on_archived"
                        should_stop_crawl = True
                        self._print_progress(
                            tag_name=vtb_config.name,
                            message=(
                                f"stop on archived page={page_index} cover={cover_index} "
                                f"post_id={cover_item.post_id or '-'} archive_key={archive_item_id}"
                            ),
                        )
                        break

                    self._print_progress(
                        tag_name=vtb_config.name,
                        message=(
                            f"scrape detail page={page_index} cover={cover_index} "
                            f"post_id={cover_item.post_id or '-'} url={cover_item.detail_url}"
                        ),
                    )
                    detail_page_result = self._detail_page_scraper.scrape_detail_page(
                        page_url=cover_item.detail_url,
                        is_headless=is_headless,
                        timeout_milliseconds=timeout_milliseconds,
                        browser_session=browser_session,
                    )
                    saved_detail_file_path = save_manager.save_cover_detail_result(
                        cover_item=cover_item,
                        detail_page_result=detail_page_result,
                    )
                    saved_detail_count += 1
                    self._print_progress(
                        tag_name=vtb_config.name,
                        message=(
                            f"saved detail page={page_index} cover={cover_index} "
                            f"access_status={detail_page_result.access_status} file={saved_detail_file_path}"
                        ),
                    )

                    if self._should_add_to_archive(detail_page_result):
                        archive_added = self._add_archive_item_immediately(
                            archive_manager=archive_manager,
                            archive_item_id=archive_item_id,
                        )
                        if archive_added:
                            archive_added_count += 1
                        self._print_progress(
                            tag_name=vtb_config.name,
                            message=(
                                f"archive committed key={archive_item_id}"
                                if archive_added
                                else f"archive already exists key={archive_item_id}"
                            ),
                        )

                    log_file_path = log_manager.append(
                        LogRecord(
                            tag_name=current_tag_page_result.tag_name,
                            published_at=detail_page_result.published_at or cover_item.published_at,
                            saved_detail_file_path=str(saved_detail_file_path),
                            download_links=detail_page_result.download_links,
                        )
                    )
                    self._print_progress(
                        tag_name=vtb_config.name,
                        message=f"log appended file={log_file_path}",
                    )

                    if detail_page_result.access_status == "daily_limit_reached":
                        stopped_reason = "daily_limit_reached"
                        should_stop_crawl = True
                        self._print_progress(
                            tag_name=vtb_config.name,
                            message="stop on daily limit reached",
                        )
                        break

                if should_stop_crawl:
                    break
        finally:
            self._browser_client.close_browser_session(browser_session)

        self._print_progress(
            tag_name=vtb_config.name,
            message=f"archive committed count={archive_added_count}",
        )
        self._print_progress(
            tag_name=vtb_config.name,
            message=(
                f"completed processed_page_count={processed_page_count} "
                f"processed_cover_count={processed_cover_count} "
                f"saved_detail_count={saved_detail_count} "
                f"skipped_archived_count={skipped_archived_count} "
                f"archive_added_count={archive_added_count} "
                f"stopped_reason={stopped_reason} "
                f"log_file={log_manager.log_file_path}"
            ),
        )
        return VtbCrawlSummary(
            tag_name=vtb_config.name,
            crawl_mode=crawl_mode.value,
            page_order=page_order.value,
            processed_page_count=processed_page_count,
            processed_cover_count=processed_cover_count,
            saved_detail_count=saved_detail_count,
            skipped_archived_count=skipped_archived_count,
            archive_added_count=archive_added_count,
            stopped_reason=stopped_reason,
            log_file_path=str(log_manager.log_file_path),
        )

    def crawl_vtb_list(
        self,
        tag_names: list[str] | None = None,
        *,
        crawl_mode: CrawlMode = CrawlMode.SKIP_ARCHIVED,
        page_order: PageOrder = PageOrder.ASCENDING,
        log_file_name: str | None = None,
        is_headless: bool = True,
        timeout_milliseconds: int = 60000,
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> BatchCrawlResult:
        crawl_summaries: list[VtbCrawlSummary] = []
        failed_tag_names: list[str] = []
        shared_log_manager = LogManager(
            log_file_name=log_file_name,
            config_manager=self._config_manager,
        )
        resolved_tag_names = tag_names if tag_names is not None else self._vtb_config_manager.get_all_vtb_names()
        total_count = len(resolved_tag_names)

        for current_count, tag_name in enumerate(resolved_tag_names, start=1):
            if on_progress is not None:
                on_progress(tag_name, current_count, total_count)
            self._print_batch_progress(message=f"start tag={tag_name}")
            try:
                crawl_summary = self.crawl_single_vtb(
                    tag_name=tag_name,
                    crawl_mode=crawl_mode,
                    page_order=page_order,
                    log_file_name=shared_log_manager.log_file_name,
                    is_headless=is_headless,
                    timeout_milliseconds=timeout_milliseconds,
                )
            except AuthenticationRequiredError:
                raise
            except Exception as error:
                failed_tag_names.append(tag_name)
                self._print_batch_progress(message=f"failed tag={tag_name} error={error}")
                continue

            crawl_summaries.append(crawl_summary)
            self._print_batch_progress(
                message=f"completed tag={tag_name} stopped_reason={crawl_summary.stopped_reason}"
            )

        return BatchCrawlResult(
            crawl_summaries=crawl_summaries,
            failed_tag_names=failed_tag_names,
            log_file_path=str(shared_log_manager.log_file_path),
        )

    @staticmethod
    def _resolve_page_urls(*, first_tag_page_result: TagPageResult, page_order: PageOrder) -> list[str]:
        page_urls = [pagination_item.page_url for pagination_item in first_tag_page_result.pagination_items]
        if not page_urls:
            page_urls = [first_tag_page_result.page_url]
        if page_order == PageOrder.DESCENDING:
            return list(reversed(page_urls))
        return page_urls

    def _get_archive_item_id(self, cover_item: CoverItem) -> str:
        if cover_item.post_id:
            return cover_item.post_id
        return self._get_archive_match_value(cover_item)

    def _get_archive_match_value(self, cover_item: CoverItem) -> str:
        return self._extract_archive_item_id_from_detail_url(cover_item.detail_url)

    def _is_cover_item_archived(
        self,
        *,
        archive_manager: ArchiveManager,
        archive_item_id: str,
        archive_match_value: str,
    ) -> bool:
        archive_candidates = [
            archive_candidate
            for archive_candidate in [archive_item_id, archive_match_value]
            if archive_candidate
        ]
        if not archive_candidates:
            return False

        for archive_candidate in archive_candidates:
            if archive_manager.is_in_archive(archive_candidate):
                return True

        for archived_item_id in archive_manager.archive_item_ids:
            if any(
                self._archive_item_ids_match(archived_item_id, archive_candidate)
                for archive_candidate in archive_candidates
            ):
                return True
        return False

    def _add_archive_item_immediately(self, *, archive_manager: ArchiveManager, archive_item_id: str) -> bool:
        if not archive_item_id:
            return False
        if archive_manager.is_in_archive(archive_item_id):
            return False
        archive_manager.add_to_archive(archive_item_id)
        return True

    def _should_add_to_archive(self, detail_page_result: DetailPageResult) -> bool:
        return detail_page_result.access_status in {"available", "not_required"}

    @staticmethod
    def _print_progress(*, tag_name: str, message: str) -> None:
        print(f"[{tag_name}] {message}", flush=True)

    @staticmethod
    def _print_batch_progress(*, message: str) -> None:
        print(f"[batch] {message}", flush=True)

    @staticmethod
    def _extract_archive_item_id_from_detail_url(detail_url: str) -> str:
        detail_path = urlparse(detail_url).path.rstrip("/")
        return Path(detail_path).stem

    @staticmethod
    def _archive_item_ids_match(left_archive_item_id: str, right_archive_item_id: str) -> bool:
        normalized_left_archive_item_id = left_archive_item_id.strip()
        normalized_right_archive_item_id = right_archive_item_id.strip()

        if not normalized_left_archive_item_id or not normalized_right_archive_item_id:
            return False
        if normalized_left_archive_item_id == normalized_right_archive_item_id:
            return True
        if not normalized_left_archive_item_id.isdigit() or not normalized_right_archive_item_id.isdigit():
            return False

        if len(normalized_left_archive_item_id) > len(normalized_right_archive_item_id):
            return normalized_left_archive_item_id.endswith(normalized_right_archive_item_id)
        if len(normalized_right_archive_item_id) > len(normalized_left_archive_item_id):
            return normalized_right_archive_item_id.endswith(normalized_left_archive_item_id)
        return False
