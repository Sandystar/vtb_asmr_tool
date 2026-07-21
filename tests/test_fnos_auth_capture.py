from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

import pytest

from spider_vtbasmr_gui.integrations.netdisk.auth_capture import (
    FnosAuthCaptureService,
    _CapturedAuth,
)
from spider_vtbasmr_gui.integrations.netdisk.credential import FnosCredential, FnosCredentialStore


class FakeLocator:
    def __init__(self, page: "FakePage", selector: str) -> None:
        self._page = page
        self._selector = selector

    def count(self) -> int:
        if self._selector in {"#username", "#password", 'button[type="submit"]'}:
            return int(self._page.login_form_visible)
        return 0

    def fill(self, value: str) -> None:
        self._page.filled_values[self._selector] = value

    def click(self, **_: object) -> None:
        if self._selector == 'button[type="submit"]':
            self._page.login_submitted = True
            self._page.login_form_visible = False
            self._page.url = "http://fnos.test/"


class FakeContext:
    def cookies(self, _: list[str]) -> list[dict[str, str]]:
        return [{"name": "language", "value": "zh-CN"}]


class FakeResponse:
    def __init__(self, url: str, payload: dict[str, object]) -> None:
        self.url = url
        self._payload = payload

    def json(self) -> dict[str, object]:
        return self._payload


class FakePage:
    def __init__(self, *, emit_auth_request: bool, authorization_code: int) -> None:
        self.url = "about:blank"
        self._emit_auth_request = emit_auth_request
        self._authorization_code = authorization_code
        self._listeners: dict[str, Callable[[Any], None]] = {}
        self.goto_urls: list[str] = []
        self.login_form_visible = False
        self.login_state_waited = False
        self.login_submitted = False
        self.filled_values: dict[str, str] = {}

    def on(self, event: str, callback: Callable[[Any], None]) -> None:
        self._listeners[event] = callback

    def remove_listener(self, event: str, _: Callable[[Any], None]) -> None:
        self._listeners.pop(event, None)

    def goto(self, url: str, **_: object) -> None:
        self.goto_urls.append(url)
        self.url = url
        if url.rstrip("/").endswith("/login") and "/app-baidu-netdisk/" not in url:
            return
        if "/app-baidu-netdisk/login" not in url or not self._emit_auth_request:
            return
        list_url = (
            "http://fnos.test/app-baidu-netdisk/api/v1/p/rest/2.0/xpan/file"
            "?method=list&dir=%2F&page=1"
        )
        self._listeners["request"](
            SimpleNamespace(
                url=list_url,
                headers={
                    "authorization": "trim test-token",
                    "user-agent": "test-browser",
                },
            )
        )
        self._listeners["response"](
            FakeResponse(list_url, {"errno": self._authorization_code, "list": []})
        )
        self._listeners["response"](
            FakeResponse(
                "http://fnos.test/app-baidu-netdisk/api/v1/user/info",
                {"data": {"deviceId": "device-1", "appId": "app-1"}},
            )
        )

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    def wait_for_function(self, expression: str, **_: object) -> None:
        if "document.querySelector('#username')" in expression:
            self.login_state_waited = True
            self.login_form_visible = True
            return
        if "location.pathname" in expression and self.login_submitted:
            return
        raise TimeoutError("login state did not change")

    def wait_for_timeout(self, _: int) -> None:
        return None

    def evaluate(self, expression: str, _: object = None) -> object:
        if "navigator.userAgent" in expression:
            return "test-browser"
        return {"data": {"deviceId": "device-1", "appId": "app-1"}}


class FakeBrowserClient:
    emit_auth_request = True
    authorization_code = 0
    last_instance: "FakeBrowserClient | None" = None

    def __init__(self, browser_channel: str | None = None) -> None:
        self.browser_channel = browser_channel
        self.page = FakePage(
            emit_auth_request=self.emit_auth_request,
            authorization_code=self.authorization_code,
        )
        self.context = FakeContext()
        self.closed = False
        self.__class__.last_instance = self

    def open_browser_session(
        self,
        *,
        is_headless: bool,
        user_data_dir=None,
        profile_directory: str = "Default",
    ) -> SimpleNamespace:
        assert is_headless is True
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory
        return SimpleNamespace(page=self.page, context=self.context)

    def close_browser_session(self, _: object) -> None:
        self.closed = True


def build_store(tmp_path) -> FnosCredentialStore:
    user_data_dir = tmp_path / "edge-user-data"
    (user_data_dir / "Profile 1").mkdir(parents=True)
    store = FnosCredentialStore(tmp_path / "fnos.json")
    store.save(
        FnosCredential(
            base_url="http://fnos.test/",
            username="user",
            password="password",
            browser_type="edge",
            browser_user_data_dir=str(user_data_dir),
            browser_profile_directory="Profile 1",
            device_id=None,
        )
    )
    return store


def test_capture_uses_authorization_header_when_token_cookie_is_absent(tmp_path) -> None:
    FakeBrowserClient.emit_auth_request = True
    FakeBrowserClient.authorization_code = 0
    store = build_store(tmp_path)
    service = FnosAuthCaptureService(store, browser_factory=FakeBrowserClient)  # type: ignore[arg-type]

    captured = service.capture(timeout_milliseconds=100)

    assert captured.cookie == "language=zh-CN; fnos-token=test-token"
    assert captured.user_agent == "test-browser"
    assert captured.device_id == "device-1"
    assert captured.appid == "app-1"
    assert store.load() == captured
    assert FakeBrowserClient.last_instance is not None
    assert FakeBrowserClient.last_instance.browser_channel == "msedge"
    assert FakeBrowserClient.last_instance.user_data_dir.name == "User Data"
    assert FakeBrowserClient.last_instance.user_data_dir.exists() is False
    assert FakeBrowserClient.last_instance.profile_directory == "Profile 1"
    assert FakeBrowserClient.last_instance.closed is True
    assert FakeBrowserClient.last_instance.page.goto_urls == [
        "http://fnos.test/login",
        "http://fnos.test/app-baidu-netdisk/login",
    ]
    assert FakeBrowserClient.last_instance.page.login_state_waited is True
    assert FakeBrowserClient.last_instance.page.login_submitted is True
    assert FakeBrowserClient.last_instance.page.filled_values == {
        "#username": "user",
        "#password": "password",
    }
    assert FakeBrowserClient.last_instance.page._listeners == {}


def test_capture_reports_missing_api_auth_and_closes_browser(tmp_path) -> None:
    FakeBrowserClient.emit_auth_request = False
    FakeBrowserClient.authorization_code = 0
    service = FnosAuthCaptureService(
        build_store(tmp_path),
        browser_factory=FakeBrowserClient,  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="Authorization: trim"):
        service.capture(timeout_milliseconds=1)

    assert FakeBrowserClient.last_instance is not None
    assert FakeBrowserClient.last_instance.closed is True
    assert FakeBrowserClient.last_instance.page._listeners == {}


def test_capture_rejects_token_when_file_list_is_unauthorized(tmp_path) -> None:
    FakeBrowserClient.emit_auth_request = True
    FakeBrowserClient.authorization_code = 401
    store = build_store(tmp_path)
    service = FnosAuthCaptureService(store, browser_factory=FakeBrowserClient)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="文件列表接口"):
        service.capture(timeout_milliseconds=1)

    assert store.load().cookie is None
    assert FakeBrowserClient.last_instance is not None
    assert FakeBrowserClient.last_instance.closed is True


def test_login_state_waits_for_delayed_form_then_submits_credentials() -> None:
    page = FakePage(emit_auth_request=False, authorization_code=0)
    page.url = "http://fnos.test/login"

    FnosAuthCaptureService._ensure_fnos_login(
        page=page,
        credential=FnosCredential(username="user", password="password"),
        timeout_milliseconds=100,
    )

    assert page.login_state_waited is True
    assert page.login_submitted is True
    assert page.url == "http://fnos.test/"


def test_visible_login_waits_without_deadline_for_manual_fnos_login() -> None:
    class ManualLoginPage(FakePage):
        def __init__(self) -> None:
            super().__init__(emit_auth_request=False, authorization_code=0)
            self.url = "http://fnos.test/login"
            self.timeouts: list[int] = []

        def wait_for_function(self, expression: str, *, timeout: int) -> None:
            self.timeouts.append(timeout)
            if "document.querySelector('#username')" in expression:
                self.login_form_visible = True
            else:
                self.login_form_visible = False
                self.url = "http://fnos.test/"

    page = ManualLoginPage()
    FnosAuthCaptureService._ensure_fnos_login(
        page=page,
        credential=FnosCredential(),
        timeout_milliseconds=None,
    )

    assert page.timeouts == [0, 0]
    assert page.login_submitted is False
    assert page.url == "http://fnos.test/"


def test_headless_login_rejects_missing_credentials_after_form_renders() -> None:
    page = FakePage(emit_auth_request=False, authorization_code=0)
    page.url = "http://fnos.test/login"

    with pytest.raises(RuntimeError, match="没有自动登录账号或密码"):
        FnosAuthCaptureService._ensure_fnos_login(
            page=page,
            credential=FnosCredential(),
            timeout_milliseconds=100,
        )


def test_visible_login_stops_when_user_closes_browser() -> None:
    class ClosedLoginPage:
        url = "http://fnos.test/login"

        def wait_for_function(self, _: str, **__: object) -> None:
            raise RuntimeError("Target page has been closed")

        def is_closed(self) -> bool:
            return True

    with pytest.raises(RuntimeError, match="浏览器窗口已关闭"):
        FnosAuthCaptureService._ensure_fnos_login(
            page=ClosedLoginPage(),
            credential=FnosCredential(),
            timeout_milliseconds=None,
        )


def test_visible_capture_waits_without_deadline_until_manual_login() -> None:
    captured = _CapturedAuth()

    class DelayedAuthPage:
        def __init__(self) -> None:
            self.wait_count = 0

        def is_closed(self) -> bool:
            return False

        def wait_for_timeout(self, _: int) -> None:
            self.wait_count += 1
            if self.wait_count == 3:
                captured.token = "manual-token"
                captured.authorized = True

    page = DelayedAuthPage()
    FnosAuthCaptureService._wait_for_authorized_token(
        page=page,
        captured=captured,
        timeout_milliseconds=None,
    )

    assert page.wait_count == 3


def test_visible_capture_stops_when_user_closes_browser() -> None:
    page = SimpleNamespace(is_closed=lambda: True)

    with pytest.raises(RuntimeError, match="浏览器窗口已关闭"):
        FnosAuthCaptureService._wait_for_authorized_token(
            page=page,
            captured=_CapturedAuth(),
            timeout_milliseconds=None,
        )
