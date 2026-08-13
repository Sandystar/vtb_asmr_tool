from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from spider_vtbasmr_gui.config import AppConfig
from spider_vtbasmr_gui.config.fnos_config import FnosConfig
from spider_vtbasmr_gui.services.resource_transfer_service import ResourceTransferService


class StaticContextProvider:
    def __init__(self, config: AppConfig) -> None:
        self._context = SimpleNamespace(app_config=config)

    def require(self) -> Any:
        return self._context


class RecordingNetdiskClient:
    def __init__(self) -> None:
        self.created: list[str] = []
        self.transferred: list[tuple[str, str]] = []
        self.downloads: list[tuple[str, list[str]]] = []

    def create_folder(self, path: str) -> None:
        self.created.append(path)

    def transfer_share_all(self, link: str, target: str) -> None:
        self.transferred.append((link, target))

    def download_by_paths(self, target: str, paths: list[str]) -> None:
        self.downloads.append((target, paths))


def test_parse_and_transfer_resource_flow_uses_injected_client(tmp_path: Path) -> None:
    log_path = tmp_path / "crawl.json"
    log_path.write_text(
        json.dumps(
            [
                {
                    "tag_name": "Example",
                    "published_at": "2026-03-14",
                    "saved_detail_file_path": ".data/save/Example/123.json",
                    "download_links": [
                        {"link_url": "https://pan.baidu.com/s/1abc?pwd=1234"},
                        {"link_url": ""},
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )
    provider = StaticContextProvider(
        AppConfig(
            fnos_config=FnosConfig(
                transfer_root_dir="/vtbasmr",
                nas_download_dir="/nas/download",
            )
        )
    )
    client = RecordingNetdiskClient()
    service = ResourceTransferService(
        provider,  # type: ignore[arg-type]
        client_factory=lambda _: client,  # type: ignore[arg-type,return-value]
    )

    parsed = service.parse_log_file(log_path)
    result = service.transfer_resources(parsed.resource_items)

    assert len(parsed.resource_items) == 1
    assert client.created == result.transferred_paths
    assert client.transferred[0][0] == "https://pan.baidu.com/s/1abc?pwd=1234"
    assert client.downloads == [("/nas/download", [result.batch_root_path])]
    assert "/Example/123/2026-03-14" in result.transferred_paths[0]