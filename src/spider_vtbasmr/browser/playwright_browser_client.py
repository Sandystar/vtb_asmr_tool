from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Error as PlaywrightError, Page, Playwright, sync_playwright

from spider_vtbasmr.manager.config_manager import ConfigManager


@dataclass(slots=True)
class BrowserSession:
    playwright: Playwright
    playwright_driver: Any
    browser: Browser | None
    context: BrowserContext
    page: Page


class PlaywrightBrowserClient:
    def __init__(self, *, config_manager: ConfigManager | None = None) -> None:
        self._config_manager = config_manager

    def open_browser_session(self, *, is_headless: bool = False) -> BrowserSession:
        playwright_driver = sync_playwright()
        playwright = playwright_driver.start()

        try:
            browser = self._launch_browser(playwright=playwright, is_headless=is_headless)
            context = browser.new_context()
            page = self._create_controlled_page(context)
        except Exception:
            playwright.stop()
            raise

        return BrowserSession(
            playwright=playwright,
            playwright_driver=playwright_driver,
            browser=browser,
            context=context,
            page=page,
        )

    def open_logged_in_browser_session(
        self,
        *,
        storage_state: dict[str, object],
        is_headless: bool = False,
    ) -> BrowserSession:
        if not storage_state:
            raise ValueError("Login state is empty. Please log in again.")
        browser_session = self.open_browser_session(is_headless=is_headless)
        if browser_session.browser is None:
            raise RuntimeError("A managed browser instance is required to restore storage state")
        browser_session.context.close()
        browser_session.context = browser_session.browser.new_context(storage_state=storage_state)
        browser_session.page = browser_session.context.new_page()
        return browser_session

    def save_storage_state(self, browser_session: BrowserSession) -> dict[str, object]:
        try:
            state = browser_session.context.storage_state()
        except PlaywrightError as error:
            raise RuntimeError(
                "登录窗口已被关闭，无法保存登录状态。请保持登录窗口开启，等待程序自动关闭。"
            ) from error
        if not isinstance(state, dict):
            raise RuntimeError("Playwright returned an invalid login state")
        return state

    def close_browser_session(self, browser_session: BrowserSession) -> None:
        try:
            browser_session.context.close()
        except PlaywrightError:
            pass
        if browser_session.browser is not None:
            try:
                browser_session.browser.close()
            except PlaywrightError:
                pass
        browser_session.playwright.stop()

    @staticmethod
    def _create_controlled_page(context: BrowserContext) -> Page:
        page = context.new_page()
        for startup_page in tuple(context.pages):
            if startup_page is page:
                continue
            try:
                startup_page.close()
            except PlaywrightError:
                pass
        return page

    @staticmethod
    def _launch_browser(playwright: Playwright, is_headless: bool) -> Browser:
        try:
            return playwright.chromium.launch(headless=is_headless)
        except PlaywrightError as error:
            raise RuntimeError(
                "Unable to launch Playwright Chromium. "
                "Run `python -m playwright install chromium` before starting the application."
            ) from error