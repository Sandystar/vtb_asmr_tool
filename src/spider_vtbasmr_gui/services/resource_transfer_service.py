from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from spider_vtbasmr_gui.integrations.netdisk import (
    FnosAuthCaptureService,
    NetdiskClient,
    NetdiskGateway,
)
from spider_vtbasmr_gui.services.runtime_context import RuntimeContext, RuntimeContextProvider


@dataclass(frozen=True, slots=True)
class TransferResourceItem:
    tag_name: str
    published_at: str
    detail_file_stem: str
    link_url: str


@dataclass(frozen=True, slots=True)
class ParsedResourceLogResult:
    log_file_path: str
    resource_items: list[TransferResourceItem]
    summary_text: str


@dataclass(frozen=True, slots=True)
class ResourceTransferResult:
    batch_root_path: str
    download_target_path: str
    transferred_paths: list[str]
    summary_text: str


class ResourceTransferService:
    def __init__(
        self,
        context_provider: RuntimeContextProvider,
        *,
        client_factory: Callable[[RuntimeContext], NetdiskClient] | None = None,
        capture_factory: Callable[[RuntimeContext], FnosAuthCaptureService] | None = None,
    ) -> None:
        self._context_provider = context_provider
        self._client_factory = client_factory or self._build_client
        self._capture_factory = capture_factory or self._build_capture

    def default_log_directory(self) -> Path:
        return self._context_provider.require().spider_config.get_log_dir_path()

    def capture_fnos_auth(self) -> str:
        context = self._context_provider.require()
        self._capture_factory(context).capture(is_headless=False)
        return "FNOS 登录完成，认证配置已更新。"

    def parse_log_file(self, log_file_path: str | Path) -> ParsedResourceLogResult:
        path = Path(log_file_path).expanduser().resolve(strict=False)
        if not path.is_file() or path.suffix.lower() != ".json":
            raise ValueError(f"请选择有效的 JSON 日志文件: {path}")
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list):
            raise ValueError("抓取日志必须是 JSON array")
        items = [
            TransferResourceItem(
                tag_name=tag_name,
                published_at=published_at,
                detail_file_stem=detail_stem,
                link_url=link_url,
            )
            for record in payload
            if isinstance(record, dict)
            for tag_name in [str(record.get("tag_name") or "").strip()]
            for published_at in [str(record.get("published_at") or "").strip()]
            for detail_stem in [Path(str(record.get("saved_detail_file_path") or "")).stem.strip()]
            for links in [record.get("download_links")]
            if tag_name and published_at and detail_stem and isinstance(links, list)
            for link in links
            if isinstance(link, dict)
            for link_url in [str(link.get("link_url") or "").strip()]
            if link_url
        ]
        return ParsedResourceLogResult(
            log_file_path=str(path),
            resource_items=items,
            summary_text=f"解析完成，共获得 {len(items)} 条可转存资源。",
        )

    def transfer_resources(self, items: list[TransferResourceItem]) -> ResourceTransferResult:
        if not items:
            raise ValueError("没有可转存资源")
        context = self._context_provider.require()
        fnos_config = context.app_config.fnos_config
        if fnos_config is None or not fnos_config.has_transfer_settings():
            raise ValueError("请先配置网盘转存目录和 NAS 下载目录")
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        parent = self._netdisk_path(fnos_config.transfer_root_dir or "/")
        batch_root = self._join_path(parent, timestamp)
        client = self._client_factory(context)
        transferred: list[str] = []
        for item in items:
            target = self._join_path(
                batch_root,
                item.tag_name,
                item.detail_file_stem,
                item.published_at,
            )
            client.create_folder(target)
            client.transfer_share_all(item.link_url, target)
            transferred.append(target)
        client.download_by_paths(fnos_config.nas_download_dir or "", [batch_root])
        return ResourceTransferResult(
            batch_root_path=batch_root,
            download_target_path=fnos_config.nas_download_dir or "",
            transferred_paths=transferred,
            summary_text=f"已转存 {len(transferred)} 条资源，并提交 NAS 下载：{batch_root}",
        )

    @staticmethod
    def _build_client(context: RuntimeContext) -> NetdiskClient:
        credential = context.credential_store.load()
        return NetdiskClient(NetdiskGateway(credential))

    @staticmethod
    def _build_capture(context: RuntimeContext) -> FnosAuthCaptureService:
        return FnosAuthCaptureService(context.credential_store)

    @staticmethod
    def _netdisk_path(path: str) -> str:
        return "/" + "/".join(part for part in path.replace("\\", "/").split("/") if part)

    @classmethod
    def _join_path(cls, *parts: str) -> str:
        return cls._netdisk_path("/".join(parts))