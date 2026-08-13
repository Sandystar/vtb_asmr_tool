from __future__ import annotations

from dataclasses import dataclass

from spider_vtbasmr.browser.playwright_browser_client import BrowserSession, PlaywrightBrowserClient
from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.login_action import LoginAction


@dataclass(slots=True)
class LoginResult:
    login_url: str
    final_url: str


class LoginStateManager:
    def __init__(
        self,
        login_url: str | None = None,
        browser_client: PlaywrightBrowserClient | None = None,
        login_action: LoginAction | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigManager()
        self._login_url = login_url or self._config_manager.get_login_url()
        self._browser_client = browser_client or PlaywrightBrowserClient(
            config_manager=self._config_manager,
        )
        self._login_action = login_action or LoginAction(
            config_manager=self._config_manager,
        )

    def create_login_state(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        is_headless: bool = True,
        timeout_milliseconds: int = 30000,
    ) -> LoginResult:
        login_username = username or self._config_manager.get_login_username()
        login_password = password or self._config_manager.get_login_password()
        browser_session: BrowserSession | None = None

        try:
            browser_session = self._browser_client.open_browser_session(is_headless=is_headless)
            self._login_action.perform_login(
                page=browser_session.page,
                login_url=self._login_url,
                username=login_username,
                password=login_password,
                timeout_milliseconds=timeout_milliseconds,
            )
            storage_state = self._browser_client.save_storage_state(browser_session)
            self._config_manager.save_storage_state(storage_state)
            final_url = browser_session.page.url
        finally:
            if browser_session is not None:
                self._browser_client.close_browser_session(browser_session)

        return LoginResult(login_url=self._login_url, final_url=final_url)