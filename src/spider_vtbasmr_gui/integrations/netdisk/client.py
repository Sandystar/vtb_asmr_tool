from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

from spider_vtbasmr_gui.integrations.netdisk.gateway import NetdiskGateway, NetdiskGatewayError


class NetdiskClient:
    _FILE_ENDPOINT = "/app-baidu-netdisk/api/v1/p/rest/2.0/xpan/file"
    _SHARE_ENDPOINT = "/app-baidu-netdisk/api/v1/p/apaas/1.0/share"

    def __init__(self, gateway: NetdiskGateway) -> None:
        self._gateway = gateway

    def create_folder(self, folder_path: str, *, rtype: int = 0) -> dict[str, Any]:
        path = self._normalize_path(folder_path)
        if path == "/":
            raise ValueError("不能创建网盘根目录")
        return self._request(
            "创建目录",
            method="POST",
            path=self._FILE_ENDPOINT,
            params={"method": "create"},
            form_data={"path": path, "isdir": 1, "rtype": rtype},
        )

    def transfer_share_all(
        self,
        share_url: str,
        to_path: str,
        *,
        async_mode: int = 2,
        ondup: str = "newcopy",
    ) -> dict[str, Any]:
        short_url, password = self._parse_share_url(share_url)
        verify_payload = self._verify_share(short_url, password)
        spwd = self._extract_spwd(verify_payload)
        list_payload = self._list_share(short_url, spwd)
        fsids = [
            str(item.get("fsid", item.get("fs_id"))).strip()
            for item in self._extract_items(list_payload)
            if item.get("fsid", item.get("fs_id")) is not None
        ]
        if not fsids:
            raise NetdiskGatewayError("分享链接中没有可转存资源")
        return self._request(
            "转存分享资源",
            method="POST",
            path=f"{self._SHARE_ENDPOINT}/transfer",
            params={
                "short_url": short_url,
                "device_id": self._gateway.device_id,
                "appid": self._gateway.appid,
                "product": self._gateway.product,
            },
            form_data={
                "fsid_list": json.dumps(fsids, ensure_ascii=False),
                "to_path": self._normalize_path(to_path),
                "spwd": spwd,
                "async": async_mode,
                "ondup": ondup,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        )

    def download_by_paths(
        self,
        target_path: str,
        path_list: list[str],
        *,
        rtype: int = 1,
    ) -> dict[str, Any]:
        path_to_id, failed_paths = self.resolve_file_ids(path_list)
        if failed_paths:
            raise ValueError(f"无法解析网盘路径: {', '.join(failed_paths)}")
        return self._request(
            "提交 NAS 下载",
            method="POST",
            path="/app-baidu-netdisk/api/v1/fileTask/downloadToNas",
            json_data={
                "targetPath": target_path,
                "fsIds": list(path_to_id.values()),
                "rtype": rtype,
            },
        )

    def resolve_file_ids(self, path_list: list[str]) -> tuple[dict[str, int], list[str]]:
        pending: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        failed: list[str] = []
        for raw_path in path_list:
            path = self._normalize_path(raw_path)
            pure_path = PurePosixPath(path)
            if path == "/" or not pure_path.name:
                failed.append(raw_path)
                continue
            parent = str(pure_path.parent) or "/"
            pending[parent][pure_path.name].append(path)

        resolved: dict[str, int] = {}
        for parent, targets in pending.items():
            unresolved = set(targets)
            page = 1
            while unresolved:
                payload = self._list_files(parent, page=page, page_size=1000)
                items = self._extract_items(payload)
                if not items:
                    break
                for item in items:
                    name = str(item.get("server_filename") or "")
                    if name not in unresolved:
                        continue
                    try:
                        file_id = int(item.get("fs_id"))
                    except (TypeError, ValueError):
                        continue
                    for path in targets[name]:
                        resolved[path] = file_id
                    unresolved.discard(name)
                if len(items) < 1000:
                    break
                page += 1
            for name in unresolved:
                failed.extend(targets[name])
        return resolved, failed

    def _verify_share(self, short_url: str, password: str) -> dict[str, Any]:
        return self._request(
            "验证分享链接",
            method="POST",
            path=f"{self._SHARE_ENDPOINT}/verify",
            params={
                "short_url": short_url,
                "appid": self._gateway.appid,
                "product": self._gateway.product,
            },
            form_data={"pwd": password},
        )

    def _list_share(self, short_url: str, spwd: str) -> dict[str, Any]:
        return self._request(
            "列出分享资源",
            method="POST",
            path=f"{self._SHARE_ENDPOINT}/list",
            params={
                "short_url": short_url,
                "appid": self._gateway.appid,
                "product": self._gateway.product,
            },
            form_data={
                "page_size": 100,
                "t": int(time.time() * 1000),
                "dir": "/",
                "order_by": "time",
                "desc_order": 1,
                "spwd": spwd,
                "page": 1,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        )

    def _list_files(self, directory: str, *, page: int, page_size: int) -> dict[str, Any]:
        return self._request(
            "列出网盘目录",
            method="GET",
            path=self._FILE_ENDPOINT,
            params={
                "method": "list",
                "web": 1,
                "num": page_size,
                "dir": directory,
                "order": "name",
                "desc": 0,
                "page": page,
            },
        )

    def _request(self, action: str, **request: Any) -> dict[str, Any]:
        payload = self._gateway.request_json(**request)
        raw_code = payload.get("errno", payload.get("code"))
        try:
            code = int(raw_code)
        except (TypeError, ValueError) as error:
            raise NetdiskGatewayError(f"{action}失败: 响应缺少状态码") from error
        if code != 0:
            raise NetdiskGatewayError(f"{action}失败: code={code}")
        return payload

    @staticmethod
    def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        raw_items = data.get("list", []) if isinstance(data, dict) else payload.get("list", [])
        return [item for item in raw_items if isinstance(item, dict)] if isinstance(raw_items, list) else []

    @staticmethod
    def _extract_spwd(payload: dict[str, Any]) -> str:
        data = payload.get("data")
        candidates = [payload.get("spwd"), payload.get("randsk")]
        if isinstance(data, dict):
            candidates.extend([data.get("spwd"), data.get("randsk")])
        for value in candidates:
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise NetdiskGatewayError("验证分享链接失败: 响应缺少 spwd")

    @staticmethod
    def _parse_share_url(share_url: str) -> tuple[str, str]:
        parsed = urlparse(share_url.strip())
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[0] != "s":
            raise ValueError("百度网盘分享链接格式无效")
        share_id = parts[-1]
        short_url = share_id[1:] if share_id.startswith("1") else share_id
        password = parse_qs(parsed.query).get("pwd", [""])[0].strip()
        if password and len(password) != 4:
            raise ValueError("分享链接提取码必须是 4 个字符")
        return short_url, password

    @staticmethod
    def _normalize_path(path_value: str) -> str:
        segments = [part for part in str(path_value).replace("\\", "/").split("/") if part]
        return "/" + "/".join(segments) if segments else "/"