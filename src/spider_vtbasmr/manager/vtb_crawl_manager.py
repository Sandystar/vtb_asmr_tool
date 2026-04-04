from __future__ import annotations

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
from spider_vtbasmr.scraper.tag_page_scraper import CoverItem, TagPageScraper


class CrawlMode(str, Enum):
    ALL = "all"
    SKIP_ARCHIVED = "skip_archived"
    UNTIL_ARCHIVED = "until_archived"


@dataclass(slots=True)
class VtbCrawlSummary:
    tag_name: str
    crawl_mode: str
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
            "processed_page_count": self.processed_page_count,
            "processed_cover_count": self.processed_cover_count,
            "saved_detail_count": self.saved_detail_count,
            "skipped_archived_count": self.skipped_archived_count,
            "archive_added_count": self.archive_added_count,
            "stopped_reason": self.stopped_reason,
            "log_file_path": self.log_file_path,
        }


class VtbCrawlManager:
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
        self._browser_client = browser_client or PlaywrightBrowserClient()
        self._tag_page_scraper = tag_page_scraper or TagPageScraper(browser_client=self._browser_client)
        self._detail_page_scraper = detail_page_scraper or DetailPageScraper(browser_client=self._browser_client)

    def crawl_vtb(
        self,
        tag_name: str,
        *,
        crawl_mode: CrawlMode = CrawlMode.SKIP_ARCHIVED,
        is_headless: bool = True,
        timeout_milliseconds: int = 60000,
    ) -> VtbCrawlSummary:
        vtb_config = self._vtb_config_manager.get_vtb_config(tag_name)
        archive_manager = ArchiveManager(vtb_config.archive_file_path)
        save_manager = SaveManager(vtb_config.save_dir_path)
        log_manager = LogManager(vtb_config.log_file_path)
        log_records: list[LogRecord] = []
        pending_archive_item_ids: list[str] = []
        login_state_path = self._config_manager.get_login_state_file_path()

        self._print_progress(
            tag_name=vtb_config.name,
            message=(
                f"prepare crawl_mode={crawl_mode.value} first_page={vtb_config.url} "
                f"login_state={login_state_path}"
            ),
        )
        browser_session = self._browser_client.open_logged_in_browser_session(
            storage_state_path=login_state_path,
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
            page_urls = [pagination_item.page_url for pagination_item in first_tag_page_result.pagination_items]

            self._print_progress(
                tag_name=vtb_config.name,
                message=(
                    f"start crawl_mode={crawl_mode.value} page_count={len(page_urls)} "
                    f"login_state={login_state_path}"
                ),
            )

            for page_index, page_url in enumerate(page_urls, start=1):
                if page_index == 1:
                    current_tag_page_result = first_tag_page_result
                else:
                    current_tag_page_result = self._tag_page_scraper.scrape_tag_page(
                        page_url=page_url,
                        is_headless=is_headless,
                        timeout_milliseconds=timeout_milliseconds,
                        browser_session=browser_session,
                    )

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
                        pending_archive_item_ids=pending_archive_item_ids,
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
                    log_records.append(
                        LogRecord(
                            tag_name=current_tag_page_result.tag_name,
                            published_at=detail_page_result.published_at or cover_item.published_at,
                            saved_detail_file_path=str(saved_detail_file_path),
                            download_links=detail_page_result.download_links,
                        )
                    )
                    self._print_progress(
                        tag_name=vtb_config.name,
                        message=(
                            f"saved detail page={page_index} cover={cover_index} "
                            f"access_status={detail_page_result.access_status} file={saved_detail_file_path}"
                        ),
                    )

                    if self._should_add_to_archive(detail_page_result):
                        self._add_pending_archive_item(
                            pending_archive_item_ids=pending_archive_item_ids,
                            archive_item_id=archive_item_id,
                        )
                        self._print_progress(
                            tag_name=vtb_config.name,
                            message=f"archive pending key={archive_item_id}",
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

        log_file_path = log_manager.save(log_records)
        if stopped_reason == "completed":
            for archive_item_id in pending_archive_item_ids:
                archive_manager.add_to_archive(archive_item_id)
                archive_added_count += 1
            self._print_progress(
                tag_name=vtb_config.name,
                message=f"archive committed count={archive_added_count}",
            )
        else:
            self._print_progress(
                tag_name=vtb_config.name,
                message=f"archive skipped stopped_reason={stopped_reason} pending_count={len(pending_archive_item_ids)}",
            )
        self._print_progress(
            tag_name=vtb_config.name,
            message=(
                f"completed processed_page_count={processed_page_count} "
                f"processed_cover_count={processed_cover_count} "
                f"saved_detail_count={saved_detail_count} "
                f"skipped_archived_count={skipped_archived_count} "
                f"archive_added_count={archive_added_count} "
                f"stopped_reason={stopped_reason} log_file={log_file_path}"
            ),
        )
        return VtbCrawlSummary(
            tag_name=vtb_config.name,
            crawl_mode=crawl_mode.value,
            processed_page_count=processed_page_count,
            processed_cover_count=processed_cover_count,
            saved_detail_count=saved_detail_count,
            skipped_archived_count=skipped_archived_count,
            archive_added_count=archive_added_count,
            stopped_reason=stopped_reason,
            log_file_path=str(log_file_path),
        )

    def _get_archive_item_id(self, cover_item: CoverItem) -> str:
        if cover_item.post_id:
            return cover_item.post_id
        return self._get_archive_match_value(cover_item)

    def _get_archive_match_value(self, cover_item: CoverItem) -> str:
        detail_path = urlparse(cover_item.detail_url).path.rstrip("/")
        return Path(detail_path).stem

    def _is_cover_item_archived(
        self,
        *,
        archive_manager: ArchiveManager,
        archive_item_id: str,
        archive_match_value: str,
        pending_archive_item_ids: list[str],
    ) -> bool:
        if archive_item_id in pending_archive_item_ids:
            return True
        if archive_manager.is_in_archive(archive_item_id):
            return True
        if archive_match_value and archive_manager.is_in_archive(archive_match_value):
            return True
        if not archive_item_id:
            return False

        for archived_item_id in archive_manager.archive_item_ids:
            if not archived_item_id.isdigit():
                continue
            if len(archived_item_id) <= len(archive_item_id):
                continue
            if archived_item_id.endswith(archive_item_id):
                return True
        return False

    def _add_pending_archive_item(self, *, pending_archive_item_ids: list[str], archive_item_id: str) -> None:
        if not archive_item_id:
            return
        if archive_item_id in pending_archive_item_ids:
            return
        pending_archive_item_ids.append(archive_item_id)

    def _should_add_to_archive(self, detail_page_result: DetailPageResult) -> bool:
        return detail_page_result.access_status in {"available", "not_required"}

    def _print_progress(self, *, tag_name: str, message: str) -> None:
        print(f"[{tag_name}] {message}", flush=True)
