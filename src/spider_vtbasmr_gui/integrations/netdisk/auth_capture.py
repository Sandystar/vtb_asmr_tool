from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import parse_qs, urlparse

from spider_vtbasmr.browser.playwright_browser_client import PlaywrightBrowserClient
from spider_vtbasmr.browser.profile_snapshot import create_browser_profile_snapshot
from spider_vtbasmr_gui.integrations.netdisk.credential import FnosCredential, FnosCredentialStore


@dataclass(slots=True)
class _CapturedAuth:
    cookie_header: str = ""
    token: str = ""
    user_agent: str = ""
    device_id: str = ""
    appid: str = ""
    authorized: bool = False


class FnosAuthCaptureService:
    def __init__(
        self,
        credential_store: FnosCredentialStore,
        *,
        browser_factory: type[PlaywrightBrowserClient] = PlaywrightBrowserClient,
    ) -> None:
        self._credential_store = credential_store
        self._browser_factory = browser_factory

    def capture(self, *, is_headless: bool = True, timeout_milliseconds: int = 60000) -> FnosCredential:
        credential = self._credential_store.load()
        if not credential.base_url:
            raise ValueError("FNOS 配置缺少 base_url")

        browser_channel = self._browser_channel(credential.browser_type)
        browser_client = self._browser_factory(browser_channel=browser_channel)
        user_data_dir = (
            self._browser_user_data_dir(credential, browser_channel)
            if credential.use_existing_browser_profile
            else None
        )
        profile_snapshot = (
            create_browser_profile_snapshot(
                user_data_dir,
                credential.browser_profile_directory,
            )
            if user_data_dir is not None
            else None
        )
        try:
            session = browser_client.open_browser_session(
                is_headless=is_headless,
                user_data_dir=(profile_snapshot.user_data_dir if profile_snapshot else None),
                profile_directory=credential.browser_profile_directory,
            )
        except Exception:
            if profile_snapshot is not None:
                profile_snapshot.cleanup()
            raise
        page = session.page
        base_url = self._origin(credential.base_url)
        captured = _CapturedAuth(
            device_id=str(credential.device_id or "").strip(),
            appid=credential.appid,
        )

        def handle_request(request: Any) -> None:
            if not self._is_authorized_api_url(request.url, base_url):
                return
            try:
                headers = {key.lower(): value for key, value in request.headers.items()}
            except Exception:
                return

            request_cookie = headers.get("cookie", "")
            context_cookie = self._context_cookie_header(session.context, base_url)
            cookie_header = self._merge_cookie_headers(context_cookie, request_cookie)
            token = self._cookie_value(cookie_header, "fnos-token") or self._authorization_token(
                headers.get("authorization", "")
            )
            if token:
                captured.token = token
                captured.cookie_header = self._with_cookie_value(
                    cookie_header,
                    "fnos-token",
                    token,
                )
            if headers.get("user-agent"):
                captured.user_agent = headers["user-agent"]

            query = parse_qs(urlparse(request.url).query)
            if query.get("device_id", [""])[0]:
                captured.device_id = query["device_id"][0].strip()
            if query.get("appid", [""])[0]:
                captured.appid = query["appid"][0].strip()

        def handle_response(response: Any) -> None:
            is_authorization_response = self._is_authorized_api_url(response.url, base_url)
            is_user_info_response = self._is_user_info_url(response.url, base_url)
            if not is_authorization_response and not is_user_info_response:
                return
            try:
                payload = response.json()
            except Exception:
                return

            if is_authorization_response:
                raw_code = payload.get("errno", payload.get("code")) if isinstance(payload, dict) else None
                try:
                    captured.authorized = int(raw_code) == 0
                except (TypeError, ValueError):
                    captured.authorized = False
            if not is_user_info_response:
                return

            device_id = self._nested_value(payload, "deviceId")
            appid = self._nested_value(payload, "appId")
            if device_id:
                captured.device_id = str(device_id).strip()
            if appid:
                captured.appid = str(appid).strip()

        page.on("request", handle_request)
        page.on("response", handle_response)
        try:
            page.goto(
                f"{base_url}/login",
                wait_until="domcontentloaded",
                timeout=timeout_milliseconds,
            )
            self._ensure_fnos_login(
                page=page,
                credential=credential,
                timeout_milliseconds=(timeout_milliseconds if is_headless else None),
            )

            page.goto(
                f"{base_url}/app-baidu-netdisk/login",
                wait_until="domcontentloaded",
                timeout=timeout_milliseconds,
            )
            self._wait_for_authorized_token(
                page=page,
                captured=captured,
                timeout_milliseconds=(timeout_milliseconds if is_headless else None),
            )

            if not captured.cookie_header:
                context_cookie = self._context_cookie_header(session.context, base_url)
                captured.cookie_header = self._with_cookie_value(
                    context_cookie,
                    "fnos-token",
                    captured.token,
                )
            if not captured.user_agent:
                captured.user_agent = str(page.evaluate("() => navigator.userAgent") or "")
            if not captured.device_id:
                user_info = self._request_json(
                    page,
                    "/app-baidu-netdisk/api/v1/user/info",
                )
                device_id = self._nested_value(user_info, "deviceId")
                appid = self._nested_value(user_info, "appId")
                if device_id:
                    captured.device_id = str(device_id).strip()
                if appid:
                    captured.appid = str(appid).strip()
            if not captured.device_id:
                raise RuntimeError("已捕获 FNOS Token，但未捕获到 device_id")

            language = self._cookie_value(captured.cookie_header, "language") or credential.language
            result = replace(
                credential,
                base_url=base_url,
                cookie=captured.cookie_header,
                user_agent=captured.user_agent,
                language=language,
                appid=captured.appid or credential.appid,
                device_id=captured.device_id,
            )
            self._credential_store.save(result)
            return result
        finally:
            try:
                page.remove_listener("request", handle_request)
                page.remove_listener("response", handle_response)
            finally:
                try:
                    browser_client.close_browser_session(session)
                finally:
                    if profile_snapshot is not None:
                        profile_snapshot.cleanup()

    @classmethod
    def _ensure_fnos_login(
        cls,
        *,
        page: Any,
        credential: FnosCredential,
        timeout_milliseconds: int | None,
    ) -> None:
        cls._wait_for_login_state(
            page=page,
            expression=r"""
                () => location.pathname.replace(/\/+$/, '') !== '/login' || (
                    document.querySelector('#username') !== null &&
                    document.querySelector('#password') !== null
                )
            """,
            timeout_milliseconds=timeout_milliseconds,
            timeout_message="FNOS 登录页未完成加载",
        )
        if not cls._is_login_url(page.url):
            return

        username = page.locator("#username")
        password = page.locator("#password")
        if not username.count() or not password.count():
            raise RuntimeError("FNOS 登录页状态异常：未找到登录表单")

        if credential.username and credential.password:
            username.fill(credential.username)
            password.fill(credential.password)
            page.locator('button[type="submit"]').click(
                timeout=(timeout_milliseconds if timeout_milliseconds is not None else 0)
            )
        elif timeout_milliseconds is not None:
            raise RuntimeError("FNOS 尚未登录，且配置中没有自动登录账号或密码")

        cls._wait_for_login_state(
            page=page,
            expression=r"() => location.pathname.replace(/\/+$/, '') !== '/login'",
            timeout_milliseconds=timeout_milliseconds,
            timeout_message="FNOS 登录未完成",
        )

    @staticmethod
    def _wait_for_login_state(
        *,
        page: Any,
        expression: str,
        timeout_milliseconds: int | None,
        timeout_message: str,
    ) -> None:
        try:
            page.wait_for_function(
                expression,
                timeout=(timeout_milliseconds if timeout_milliseconds is not None else 0),
            )
        except Exception as error:
            is_closed = getattr(page, "is_closed", None)
            if timeout_milliseconds is None or (callable(is_closed) and is_closed()):
                raise RuntimeError("浏览器窗口已关闭，FNOS 登录未完成") from error
            raise RuntimeError(f"{timeout_message}；请检查 FNOS 地址或登录配置") from error

    @staticmethod
    def _is_login_url(url: str) -> bool:
        return urlparse(url).path.rstrip("/") == "/login"

    @staticmethod
    def _wait_for_authorized_token(
        *,
        page: Any,
        captured: _CapturedAuth,
        timeout_milliseconds: int | None,
    ) -> None:
        deadline = (
            monotonic() + max(timeout_milliseconds, 1) / 1000
            if timeout_milliseconds is not None
            else None
        )
        while deadline is None or monotonic() < deadline:
            if captured.token and captured.authorized:
                return
            is_closed = getattr(page, "is_closed", None)
            if callable(is_closed) and is_closed():
                raise RuntimeError("浏览器窗口已关闭，FNOS 百度网盘认证未完成")
            try:
                page.wait_for_timeout(200)
            except Exception as error:
                if deadline is None:
                    raise RuntimeError("浏览器窗口已关闭，FNOS 百度网盘认证未完成") from error
                raise
        if captured.token:
            raise RuntimeError(
                "已观察到 FNOS Token，但百度网盘文件列表接口未确认授权成功；"
                "请在打开的窗口中完成百度网盘登录后重试"
            )
        raise RuntimeError(
            "未观察到携带 Authorization: trim ... 或 fnos-token Cookie 的百度网盘文件列表请求；"
            "请在打开的窗口中完成百度网盘登录后重试"
        )

    @staticmethod
    def _request_json(page: Any, request_path: str) -> Any | None:
        try:
            return page.evaluate(
                """
                async (requestPath) => {
                    const controller = new AbortController();
                    const timeoutId = window.setTimeout(() => controller.abort(), 5000);
                    try {
                        const response = await fetch(requestPath, {
                            credentials: 'include',
                            signal: controller.signal,
                        });
                        return await response.json();
                    } catch (_) {
                        return null;
                    } finally {
                        window.clearTimeout(timeoutId);
                    }
                }
                """,
                request_path,
            )
        except Exception:
            return None

    @classmethod
    def _is_netdisk_api_url(cls, url: str, base_url: str) -> bool:
        parsed = urlparse(url)
        target = urlparse(base_url)
        return (
            parsed.netloc == target.netloc
            and parsed.path.startswith("/app-baidu-netdisk/api/v1/")
        )

    @classmethod
    def _is_authorized_api_url(cls, url: str, base_url: str) -> bool:
        if not cls._is_netdisk_api_url(url, base_url):
            return False
        parsed = urlparse(url)
        if parsed.path != "/app-baidu-netdisk/api/v1/p/rest/2.0/xpan/file":
            return False
        return parse_qs(parsed.query).get("method", [""])[0] == "list"

    @classmethod
    def _is_user_info_url(cls, url: str, base_url: str) -> bool:
        return cls._is_netdisk_api_url(url, base_url) and urlparse(url).path.endswith(
            "/user/info"
        )

    @staticmethod
    def _authorization_token(authorization: str) -> str | None:
        scheme, separator, value = authorization.strip().partition(" ")
        if separator and scheme.lower() == "trim" and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _context_cookie_header(context: Any, base_url: str) -> str:
        try:
            cookies = context.cookies([base_url])
        except Exception:
            return ""
        return "; ".join(
            f"{item.get('name')}={item.get('value')}"
            for item in cookies
            if item.get("name")
        )

    @staticmethod
    def _merge_cookie_headers(*cookie_headers: str) -> str:
        merged: dict[str, str] = {}
        for cookie_header in cookie_headers:
            for part in cookie_header.split(";"):
                name, separator, value = part.strip().partition("=")
                if separator and name.strip():
                    merged[name.strip()] = value.strip()
        return "; ".join(f"{name}={value}" for name, value in merged.items())

    @classmethod
    def _with_cookie_value(
        cls,
        cookie_header: str,
        name: str,
        value: str,
    ) -> str:
        return cls._merge_cookie_headers(cookie_header, f"{name}={value}")

    @staticmethod
    def _origin(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

    @staticmethod
    def _browser_user_data_dir(
        credential: FnosCredential,
        browser_channel: str | None,
    ) -> Path | None:
        if credential.browser_user_data_dir:
            return Path(credential.browser_user_data_dir).expanduser().resolve(strict=False)
        default_directories = {
            "msedge": Path.home() / "AppData/Local/Microsoft/Edge/User Data",
            "chrome": Path.home() / "AppData/Local/Google/Chrome/User Data",
        }
        user_data_dir = default_directories.get(browser_channel or "")
        return user_data_dir if user_data_dir and user_data_dir.exists() else None

    @staticmethod
    def _browser_channel(browser_type: str) -> str | None:
        normalized = browser_type.strip().lower()
        if normalized in {"edge", "msedge"}:
            return "msedge"
        if normalized == "chrome":
            return "chrome"
        if normalized in {"chromium", "playwright", ""}:
            return None
        raise ValueError(f"不支持的 browser_type: {browser_type}")

    @staticmethod
    def _cookie_value(cookie_header: str, key: str) -> str | None:
        for part in cookie_header.split(";"):
            name, separator, value = part.strip().partition("=")
            if separator and name == key:
                return value.strip()
        return None

    @classmethod
    def _nested_value(cls, payload: Any, key: str) -> Any | None:
        if isinstance(payload, dict):
            if key in payload:
                return payload[key]
            for value in payload.values():
                if (result := cls._nested_value(value, key)) is not None:
                    return result
        if isinstance(payload, list):
            for value in payload:
                if (result := cls._nested_value(value, key)) is not None:
                    return result
        return None