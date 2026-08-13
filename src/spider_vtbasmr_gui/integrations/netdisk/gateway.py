from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from spider_vtbasmr_gui.config.fnos_config import FnosCredential


class NetdiskGatewayError(RuntimeError):
    pass


class NetdiskGateway:
    _DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        credential: FnosCredential,
        *,
        opener: Callable[..., Any] | None = None,
        timeout_seconds: float = 30,
    ) -> None:
        credential.require_api_access()
        self._credential = credential
        self._base_url = str(credential.base_url).rstrip("/")
        self._opener = opener or urllib.request.urlopen
        self._timeout_seconds = timeout_seconds

    @property
    def appid(self) -> str:
        return self._credential.appid

    @property
    def product(self) -> str:
        return self._credential.product

    @property
    def device_id(self) -> str:
        if not self._credential.device_id:
            raise ValueError("FNOS 认证配置缺少 device_id")
        return self._credential.device_id

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json_data: dict[str, object] | None = None,
        form_data: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"

        request_headers = self._default_headers()
        if headers:
            request_headers.update(headers)

        body: bytes | None = None
        if form_data is not None:
            body = urllib.parse.urlencode(form_data, doseq=True).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif json_data is not None:
            body = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        request = urllib.request.Request(
            url=url,
            data=body,
            headers=request_headers,
            method=method.upper(),
        )
        context = None if self._credential.verify_ssl else ssl._create_unverified_context()
        try:
            with self._opener(request, context=context, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            error.close()
            raise NetdiskGatewayError(f"FNOS 请求失败: status={error.code}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise NetdiskGatewayError("FNOS 请求失败: 网络连接异常") from error
        except json.JSONDecodeError as error:
            raise NetdiskGatewayError("FNOS 返回了无效 JSON") from error

        if not isinstance(payload, dict):
            raise NetdiskGatewayError("FNOS 响应必须是 JSON object")
        return payload

    def _default_headers(self) -> dict[str, str]:
        cookie = str(self._credential.cookie or "")
        token = self._cookie_value(cookie, "fnos-token") or cookie
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"trim {token}",
            "Cookie": cookie if ";" in cookie or "fnos-token=" in cookie else f"fnos-token={cookie}",
            "User-Agent": self._DEFAULT_USER_AGENT,
        }
        return headers

    @staticmethod
    def _cookie_value(cookie_header: str, key: str) -> str | None:
        for part in cookie_header.split(";"):
            name, separator, value = part.strip().partition("=")
            if separator and name == key:
                return value.strip()
        return None