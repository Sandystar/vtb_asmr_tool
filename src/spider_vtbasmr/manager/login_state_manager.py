from dataclasses import dataclass
from pathlib import Path

from spider_vtbasmr.browser.playwright_browser_client import PlaywrightBrowserClient
from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.login_action import LoginAction


@dataclass(slots=True)
class LoginResult:
    login_url: str
    state_path: str
    final_url: str


class LoginStateManager:
    def __init__(
        self,
        login_url: str | None = None,
        state_path: Path | None = None,
        browser_client: PlaywrightBrowserClient | None = None,
        login_action: LoginAction | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigManager()
        self._login_url = login_url or self._config_manager.get_login_url()
        self._state_path = state_path or self._config_manager.get_login_state_file_path()
        self._browser_client = browser_client or PlaywrightBrowserClient()
        self._login_action = login_action or LoginAction()

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
        browser_session = self._browser_client.open_browser_session(is_headless=is_headless)

        try:
            self._login_action.perform_login(
                page=browser_session.page,
                login_url=self._login_url,
                username=login_username,
                password=login_password,
                timeout_milliseconds=timeout_milliseconds,
            )
            self._browser_client.save_storage_state(
                browser_session=browser_session,
                state_path=self._state_path,
            )
            final_url = browser_session.page.url
        finally:
            self._browser_client.close_browser_session(browser_session)

        return LoginResult(
            login_url=self._login_url,
            state_path=str(self._state_path),
            final_url=final_url,
        )
