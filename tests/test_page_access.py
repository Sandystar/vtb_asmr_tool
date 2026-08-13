from pathlib import Path
from types import SimpleNamespace

import pytest

from spider_vtbasmr.core import VtbCrawler
from spider_vtbasmr.manager.vtb_config_manager import VtbConfig
from spider_vtbasmr.scraper.detail_page_scraper import DetailPageScraper
from spider_vtbasmr.scraper.page_access import (
    AuthenticationRequiredError,
    PageAccessError,
    PageStructureChangedError,
    ensure_authenticated_page,
)
from spider_vtbasmr.scraper.tag_page_scraper import TagPageScraper


class FakeConfigManager:
    def get_storage_state(self) -> dict[str, object] | None:
        return {"cookies": []}

    def get_site_origin(self) -> str:
        return "https://vtbasmr.cc"

    def get_resource_link_markers(self) -> tuple[str, ...]:
        return ()


class FakeLocator:
    def __init__(self, count: int) -> None:
        self._count = count

    def count(self) -> int:
        return self._count


class FakePage:
    def __init__(self, url: str, *, login_form_count: int = 0, archive_title_count: int = 0) -> None:
        self.url = url
        self._login_form_count = login_form_count
        self._archive_title_count = archive_title_count

    def goto(self, *_args, **_kwargs) -> None:
        return None

    def locator(self, selector: str) -> FakeLocator:
        counts = {
            "#loginform": self._login_form_count,
            ".archive-title": self._archive_title_count,
            ".article-title": self._archive_title_count,
        }
        return FakeLocator(counts.get(selector, 0))


def test_authenticated_page_rejects_login_redirect_with_relogin_message() -> None:
    page = FakePage("https://vtbasmr.cc/login?redirect_to=https://vtbasmr.cc/")

    with pytest.raises(AuthenticationRequiredError, match="重新登录"):
        ensure_authenticated_page(page, expected_site_origin="https://vtbasmr.cc")


def test_authenticated_page_accepts_same_origin() -> None:
    page = FakePage("https://vtbasmr.cc/tag/demo")

    ensure_authenticated_page(page, expected_site_origin="https://vtbasmr.cc")


def test_authenticated_page_rejects_unexpected_origin() -> None:
    page = FakePage("https://unexpected.test/tag/demo")

    with pytest.raises(PageAccessError, match="未配置"):
        ensure_authenticated_page(page, expected_site_origin="https://vtbasmr.cc")


def test_tag_scraper_fails_fast_when_login_state_is_invalid() -> None:
    page = FakePage("https://vtbasmr.cc/login?redirect_to=https://vtbasmr.cc/tag/demo")
    session = SimpleNamespace(page=page)
    scraper = TagPageScraper(config_manager=FakeConfigManager())

    with pytest.raises(AuthenticationRequiredError):
        scraper.scrape_tag_page("https://vtbasmr.cc/tag/demo", browser_session=session)


def test_detail_scraper_fails_fast_when_login_state_is_invalid() -> None:
    page = FakePage("https://vtbasmr.cc/login?redirect_to=https://vtbasmr.cc/123.html")
    session = SimpleNamespace(page=page)
    scraper = DetailPageScraper(config_manager=FakeConfigManager())

    with pytest.raises(AuthenticationRequiredError):
        scraper.scrape_detail_page("https://vtbasmr.cc/123.html", browser_session=session)


def test_authenticated_page_reports_missing_page_structure() -> None:
    page = FakePage("https://vtbasmr.cc/tag/demo")
    scraper = TagPageScraper(config_manager=FakeConfigManager())

    with pytest.raises(PageStructureChangedError, match="archive-title"):
        scraper.scrape_tag_page("https://vtbasmr.cc/tag/demo", browser_session=SimpleNamespace(page=page))


def test_batch_stops_after_authentication_failure(tmp_path: Path) -> None:
    class FakeBatchConfigManager:
        def get_storage_state(self) -> dict[str, object]:
            return {"cookies": []}

        def get_log_dir_path(self) -> Path:
            return tmp_path / "logs"

    class FakeVtbConfigManager:
        def get_vtb_config(self, tag_name: str) -> VtbConfig:
            return VtbConfig(
                name=tag_name,
                url=f"https://vtbasmr.cc/tag/{tag_name}",
                archive_file_path=tmp_path / f"{tag_name}.txt",
                save_dir_path=tmp_path / tag_name,
            )

        def get_all_vtb_names(self) -> list[str]:
            return ["first", "second"]

    class FailingTagScraper:
        def __init__(self) -> None:
            self.call_count = 0

        def scrape_tag_page(self, **_kwargs):
            self.call_count += 1
            raise AuthenticationRequiredError("login expired")

    class FakeBrowserClient:
        def open_logged_in_browser_session(self, **_kwargs):
            return SimpleNamespace()

        def close_browser_session(self, _session) -> None:
            return None

    tag_scraper = FailingTagScraper()
    crawler = VtbCrawler(
        vtb_config_manager=FakeVtbConfigManager(),
        tag_page_scraper=tag_scraper,
        detail_page_scraper=SimpleNamespace(),
        browser_client=FakeBrowserClient(),
        config_manager=FakeBatchConfigManager(),
    )

    progress_events: list[tuple[str, int, int]] = []
    with pytest.raises(AuthenticationRequiredError, match="login expired"):
        crawler.crawl_vtb_list(
            tag_names=["first", "second"],
            log_file_name="batch",
            on_progress=lambda name, current, total: progress_events.append(
                (name, current, total)
            ),
        )

    assert tag_scraper.call_count == 1
    assert progress_events == [("first", 1, 2)]
