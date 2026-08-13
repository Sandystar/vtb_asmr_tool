from __future__ import annotations

import json
from pathlib import Path

import pytest

from spider_vtbasmr.manager.base_config import BaseConfigStore, SpiderBaseConfig
from spider_vtbasmr.scraper.detail_page_scraper import DetailPageScraper


class MarkerConfig:
    def get_storage_state(self) -> dict[str, object] | None:
        return {"cookies": []}

    def get_site_origin(self) -> str:
        return "https://example.test"

    def get_resource_link_markers(self) -> tuple[str, ...]:
        return ("https://pan.example/s", "https://drive.example/")


def test_base_config_store_uses_current_schema_and_preserves_unknown_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config/vtbasmr_base.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "login_info": {
                    "url": "https://example.test/login",
                    "username": "user",
                    "password": "password",
                    "storage_state": {"cookies": [], "origins": []},
                    "future_login_setting": {"keep": True},
                },
                "resource_link_markers": [
                    "https://pan.example/s",
                    "https://pan.example/s",
                    "",
                ],
                "log_dir": ".data/logs",
                "future_setting": {"keep": True},
            }
        ),
        encoding="utf-8",
    )

    store = BaseConfigStore(config_path, project_root=tmp_path)
    config = store.load()
    store.save(config)

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert config.resource_link_markers == ("https://pan.example/s",)
    assert payload["resource_link_markers"] == ["https://pan.example/s"]
    assert payload["login_info"]["storage_state"] == {"cookies": [], "origins": []}
    assert payload["login_info"]["future_login_setting"] == {"keep": True}
    assert payload["future_setting"] == {"keep": True}


def test_base_config_store_atomic_write_keeps_previous_file_on_replace_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config/vtbasmr_base.json"
    store = BaseConfigStore(config_path, project_root=tmp_path)
    before = SpiderBaseConfig(
        login_url="https://before.test/login",
        username="before",
        password="password",
        resource_link_markers=("https://before.test/resource",),
        log_dir=".data/logs",
        storage_state={"cookies": []},
    )
    store.save(before)
    previous_payload = config_path.read_text(encoding="utf-8")

    def fail_replace(self: Path, _: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        store.save(
            SpiderBaseConfig(
                login_url="https://after.test/login",
                username="after",
                password="password",
                resource_link_markers=("https://after.test/resource",),
                log_dir=".data/logs",
            )
        )

    assert config_path.read_text(encoding="utf-8") == previous_payload
    assert list(config_path.parent.glob(f".{config_path.name}.*.tmp")) == []


def test_detail_scraper_matches_any_resource_marker_and_uses_generic_type() -> None:
    scraper = DetailPageScraper(config_manager=MarkerConfig())

    assert scraper._match_download_link_type("https://drive.example/file/123") == "resource"
    assert scraper._match_download_link_type("https://unknown.example/file") == ""