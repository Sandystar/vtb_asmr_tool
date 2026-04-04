from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Error as PlaywrightError, Page, Playwright, sync_playwright

from spider_vtbasmr.manager.config_manager import ConfigManager


@dataclass(slots=True)
class BrowserSession:
    playwright: Playwright
    playwright_driver: Any
    browser: Browser
    context: BrowserContext
    page: Page


class PlaywrightBrowserClient:
    def __init__(self, browser_channel: str | None = None) -> None:
        config_manager = ConfigManager()
        self._browser_channel = browser_channel or config_manager.get_browser_channel()

    def open_browser_session(self, *, is_headless: bool = False) -> BrowserSession:
        playwright_driver = sync_playwright()
        playwright = playwright_driver.start()

        try:
            browser = self._launch_browser(playwright=playwright, is_headless=is_headless)
            context = browser.new_context()
            page = context.new_page()
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
        storage_state_path: str | Path,
        is_headless: bool = False,
    ) -> BrowserSession:
        resolved_storage_state_path = Path(storage_state_path)
        if not resolved_storage_state_path.exists():
            raise FileNotFoundError(f"Login state file not found: {resolved_storage_state_path}")

        browser_session = self.open_browser_session(is_headless=is_headless)
        browser_session.context.close()
        browser_session.context = browser_session.browser.new_context(
            storage_state=str(resolved_storage_state_path)
        )
        browser_session.page = browser_session.context.new_page()
        return browser_session

    def save_storage_state(self, browser_session: BrowserSession, state_path: Path) -> None:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        browser_session.context.storage_state(path=str(state_path))

    def close_browser_session(self, browser_session: BrowserSession) -> None:
        browser_session.context.close()
        browser_session.browser.close()
        browser_session.playwright.stop()

    def _launch_browser(self, playwright: Playwright, is_headless: bool) -> Browser:
        launch_kwargs = {"headless": is_headless}
        if self._browser_channel:
            try:
                return playwright.chromium.launch(
                    channel=self._browser_channel,
                    **launch_kwargs,
                )
            except PlaywrightError:
                pass

        try:
            return playwright.chromium.launch(**launch_kwargs)
        except PlaywrightError as error:
            raise RuntimeError(
                "Unable to launch a browser. "
                "Playwright managed browsers are missing and the configured system browser channel could not be used. "
                "Try installing a supported browser or run `playwright install`."
            ) from error
