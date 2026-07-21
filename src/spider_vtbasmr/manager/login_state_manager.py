from dataclasses import dataclass
from pathlib import Path

from spider_vtbasmr.browser.playwright_browser_client import BrowserSession, PlaywrightBrowserClient
from spider_vtbasmr.browser.profile_snapshot import create_browser_profile_snapshot
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
        use_existing_profile = self._config_manager.use_existing_browser_profile()
        profile_directory = self._config_manager.get_browser_profile_directory()
        source_user_data_dir = (
            self._config_manager.get_browser_user_data_dir()
            if use_existing_profile
            else None
        )
        profile_snapshot = (
            create_browser_profile_snapshot(source_user_data_dir, profile_directory)
            if source_user_data_dir is not None
            else None
        )
        browser_session: BrowserSession | None = None

        try:
            browser_session = self._browser_client.open_browser_session(
                is_headless=is_headless,
                user_data_dir=(profile_snapshot.user_data_dir if profile_snapshot else None),
                profile_directory=profile_directory,
            )
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
            if browser_session is not None:
                self._browser_client.close_browser_session(browser_session)
            if profile_snapshot is not None:
                profile_snapshot.cleanup()

        return LoginResult(
            login_url=self._login_url,
            state_path=str(self._state_path),
            final_url=final_url,
        )
