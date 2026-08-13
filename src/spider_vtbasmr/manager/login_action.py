from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from spider_vtbasmr.manager.config_manager import ConfigManager


class LoginAction:
    def __init__(
        self,
        *,
        config_manager: ConfigManager | None = None,
    ) -> None:
        resolved_config_manager = config_manager or ConfigManager()
        self._success_site_origin = resolved_config_manager.get_site_origin()

    def perform_login(
        self,
        page: Page,
        login_url: str,
        username: str,
        password: str,
        timeout_milliseconds: int,
    ) -> None:
        page.goto(login_url, wait_until="domcontentloaded", timeout=timeout_milliseconds)
        username_locator = page.locator("#user_login")
        password_locator = page.locator("#user_pass")
        if username_locator.count() == 0 and password_locator.count() == 0:
            self._assert_login_success(page=page, timeout_milliseconds=timeout_milliseconds)
            return

        username_locator.fill(username)
        password_locator.fill(password)

        remember_me_locator = page.locator("#rememberme")
        if remember_me_locator.count() > 0:
            remember_me_locator.check()

        with page.expect_navigation(
            wait_until="networkidle",
            timeout=timeout_milliseconds,
        ):
            page.locator("#wp-submit").click()

        self._assert_login_success(page=page, timeout_milliseconds=timeout_milliseconds)

    def _assert_login_success(self, page: Page, timeout_milliseconds: int) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=timeout_milliseconds)
        except PlaywrightTimeoutError:
            pass

        current_url = page.url
        current_origin = urlparse(current_url)
        expected_origin = urlparse(self._success_site_origin)
        if (current_origin.scheme, current_origin.netloc) != (
            expected_origin.scheme,
            expected_origin.netloc,
        ):
            raise RuntimeError("Login did not reach the configured website.")

        login_form_locator = page.locator("#loginform")
        if login_form_locator.count() > 0 and "/login" in current_url:
            error_message_locator = page.locator("#login_error")
            error_message = ""
            if error_message_locator.count() > 0:
                error_message = error_message_locator.inner_text().strip()
            raise RuntimeError(f"Login appears to have failed. {error_message}".strip())
