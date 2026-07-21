from dataclasses import dataclass
from pathlib import Path
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
    def __init__(
        self,
        browser_channel: str | None = None,
        *,
        config_manager: ConfigManager | None = None,
    ) -> None:
        resolved_config_manager = config_manager or ConfigManager()
        self._browser_channel = (
            browser_channel
            if browser_channel is not None
            else resolved_config_manager.get_browser_channel()
        )

    def open_browser_session(
        self,
        *,
        is_headless: bool = False,
        user_data_dir: str | Path | None = None,
        profile_directory: str = "Default",
    ) -> BrowserSession:
        playwright_driver = sync_playwright()
        playwright = playwright_driver.start()

        try:
            if user_data_dir is None:
                browser = self._launch_browser(playwright=playwright, is_headless=is_headless)
                context = browser.new_context()
            else:
                browser = None
                context = self._launch_persistent_context(
                    playwright=playwright,
                    user_data_dir=user_data_dir,
                    profile_directory=profile_directory,
                    is_headless=is_headless,
                )
            page = context.pages[0] if context.pages else context.new_page()
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
        if browser_session.browser is None:
            raise RuntimeError("A managed browser instance is required to restore storage state")
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
        if browser_session.browser is not None:
            browser_session.browser.close()
        browser_session.playwright.stop()

    def _launch_persistent_context(
        self,
        *,
        playwright: Playwright,
        user_data_dir: str | Path,
        profile_directory: str,
        is_headless: bool,
    ) -> BrowserContext:
        resolved_user_data_dir = Path(user_data_dir).expanduser().resolve(strict=False)
        if not resolved_user_data_dir.is_dir():
            raise FileNotFoundError(f"Browser user data directory not found: {resolved_user_data_dir}")

        launch_kwargs: dict[str, Any] = {
            "headless": is_headless,
            "args": [f"--profile-directory={profile_directory}"],
        }
        if self._browser_channel:
            launch_kwargs["channel"] = self._browser_channel
        try:
            return playwright.chromium.launch_persistent_context(
                user_data_dir=str(resolved_user_data_dir),
                **launch_kwargs,
            )
        except PlaywrightError as error:
            browser_name = self._browser_channel or "Chromium"
            raise RuntimeError(
                f"Unable to open the existing {browser_name} profile '{profile_directory}'. "
                "Close every window and background process of that browser, then retry."
            ) from error

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
