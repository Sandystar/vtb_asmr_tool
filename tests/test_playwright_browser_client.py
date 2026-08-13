from types import SimpleNamespace

import pytest
from playwright.sync_api import Error as PlaywrightError

from spider_vtbasmr.browser.playwright_browser_client import PlaywrightBrowserClient


class FakePage:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeContext:
    def __init__(self, startup_pages: list[FakePage]) -> None:
        self.pages = list(startup_pages)
        self.created_page: FakePage | None = None

    def new_page(self) -> FakePage:
        self.created_page = FakePage()
        self.pages.append(self.created_page)
        return self.created_page


def test_create_controlled_page_closes_browser_startup_pages() -> None:
    startup_pages = [FakePage(), FakePage()]
    context = FakeContext(startup_pages)

    controlled_page = PlaywrightBrowserClient._create_controlled_page(context)

    assert controlled_page is context.created_page
    assert controlled_page.closed is False
    assert all(page.closed for page in startup_pages)


def test_save_storage_state_reports_closed_login_window() -> None:
    class ClosedContext:
        def storage_state(self) -> None:
            raise PlaywrightError("closed before saving")

    client = object.__new__(PlaywrightBrowserClient)
    session = SimpleNamespace(context=ClosedContext())

    with pytest.raises(RuntimeError, match="保持登录窗口开启"):
        client.save_storage_state(session)


def test_close_browser_session_tolerates_already_closed_targets() -> None:
    class ClosedTarget:
        def close(self) -> None:
            raise PlaywrightError("already closed")

    class FakePlaywright:
        def __init__(self) -> None:
            self.stopped = False

        def stop(self) -> None:
            self.stopped = True

    playwright = FakePlaywright()
    session = SimpleNamespace(
        context=ClosedTarget(),
        browser=ClosedTarget(),
        playwright=playwright,
    )
    client = object.__new__(PlaywrightBrowserClient)

    client.close_browser_session(session)

    assert playwright.stopped is True