from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from spider_vtbasmr.manager.base_config import SpiderBaseConfig
from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager
from spider_vtbasmr_gui.config import AppConfig, AppConfigManager
from spider_vtbasmr_gui.config.fnos_config import (
    FnosConfig,
    FnosConfigStore,
    FnosCredential,
    FnosCredentialStore,
)
from spider_vtbasmr_gui.config.seven_zip_config import SevenZipConfig, SevenZipConfigStore
from spider_vtbasmr_gui.config.vtb_list_config import (
    VtbListConfig,
    VtbListConfigStore,
    VtbListItem,
)
from spider_vtbasmr_gui.project_paths import ProjectPaths


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_fixed_configs(paths: ProjectPaths) -> None:
    write_json(
        paths.spider_base_config_path,
        {
            "login_info": {
                "url": "https://example.test/login",
                "username": "user",
                "password": "password",
                "storage_state": {"cookies": [], "origins": []},
            },
            "resource_link_markers": ["https://pan.example/s"],
            "log_dir": ".data/logs",
        },
    )
    write_json(
        paths.vtb_list_config_path,
        {
            "example": {
                "name": "example",
                "url": "https://example.test/tag/example",
                "archive_file_path": ".data/archive/example.txt",
                "save_dir_path": ".data/save/example",
            }
        },
    )
    write_json(
        paths.fnos_config_path,
        {
            "base_url": "http://fnos.test",
            "username": "user",
            "password": "password",
            "cookie": "opaque-cookie",
            "device_id": "device-id",
            "trans_share_dir": "/transfer",
            "download_dir": "/nas",
        },
    )
    write_json(
        paths.seven_zip_config_path,
        {
            "7z_path": "tools/7z.exe",
            "decompress_password": "archive-password",
        },
    )


def test_project_paths_expose_only_four_fixed_config_files(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert paths.spider_base_config_path == tmp_path / "config/vtbasmr_base.json"
    assert paths.vtb_list_config_path == tmp_path / "config/vtb_list.json"
    assert paths.fnos_config_path == tmp_path / "config/fnos_baidu_netdisk.json"
    assert paths.seven_zip_config_path == tmp_path / "config/7zip.json"
    assert set(paths.__dataclass_fields__) == {
        "project_root",
        "spider_base_config_path",
        "vtb_list_config_path",
        "fnos_config_path",
        "seven_zip_config_path",
    }


def test_app_config_manager_loads_four_fixed_configs(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    write_fixed_configs(paths)

    loaded = AppConfigManager(project_paths=paths).load()

    assert loaded.spider_base_config is not None
    assert loaded.spider_base_config.login_url == "https://example.test/login"
    assert loaded.spider_base_config.storage_state == {"cookies": [], "origins": []}
    assert loaded.vtb_list_config is not None
    assert [item.name for item in loaded.vtb_list_config.items] == ["example"]
    assert loaded.fnos_config is not None
    assert loaded.fnos_config.transfer_root_dir == "/transfer"
    assert loaded.seven_zip_config == SevenZipConfig(
        executable_path=tmp_path / "tools/7z.exe",
        default_password="archive-password",
    )


def test_app_config_manager_saves_fixed_files_and_preserves_hidden_fields(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    write_fixed_configs(paths)
    base_payload = json.loads(paths.spider_base_config_path.read_text(encoding="utf-8"))
    base_payload["future_setting"] = {"keep": True}
    write_json(paths.spider_base_config_path, base_payload)
    fnos_payload = json.loads(paths.fnos_config_path.read_text(encoding="utf-8"))
    fnos_payload["future_setting"] = {"keep": True}
    write_json(paths.fnos_config_path, fnos_payload)
    seven_zip_payload = json.loads(paths.seven_zip_config_path.read_text(encoding="utf-8"))
    seven_zip_payload["future_setting"] = {"keep": True}
    write_json(paths.seven_zip_config_path, seven_zip_payload)

    manager = AppConfigManager(project_paths=paths)
    loaded = manager.load()
    assert loaded.spider_base_config is not None
    assert loaded.fnos_config is not None
    submitted = replace(
        loaded,
        spider_base_config=replace(
            loaded.spider_base_config,
            username=" updated-user ",
            storage_state=None,
        ),
        vtb_list_config=VtbListConfig(
            (
                VtbListItem(
                    name="renamed",
                    url="https://example.test/tag/renamed",
                    archive_file_path=str(tmp_path / ".data/archive/renamed.txt"),
                    save_dir_path=str(tmp_path / ".data/save/renamed"),
                    tag_name="example",
                ),
            )
        ),
        fnos_config=replace(
            loaded.fnos_config,
            credential=replace(
                loaded.fnos_config.credential,
                base_url="http://updated-fnos.test",
                username="updated-user",
                password="updated-password",
                cookie="stale-cookie",
                device_id="stale-device",
            ),
            transfer_root_dir="/updated-transfer",
            nas_download_dir="/updated-nas",
        ),
        seven_zip_config=SevenZipConfig(
            executable_path=tmp_path / "thirdtool/7-Zip/7z.exe",
            default_password="updated-password",
        ),
    )

    saved = manager.save(submitted)

    saved_base = json.loads(paths.spider_base_config_path.read_text(encoding="utf-8"))
    assert saved_base["login_info"]["username"] == "updated-user"
    assert saved_base["login_info"]["storage_state"] == {"cookies": [], "origins": []}
    assert saved_base["future_setting"] == {"keep": True}
    saved_vtb = json.loads(paths.vtb_list_config_path.read_text(encoding="utf-8"))
    assert list(saved_vtb) == ["renamed"]
    assert saved_vtb["renamed"]["archive_file_path"] == ".data/archive/renamed.txt"
    saved_fnos = json.loads(paths.fnos_config_path.read_text(encoding="utf-8"))
    assert saved_fnos["cookie"] == "opaque-cookie"
    assert saved_fnos["device_id"] == "device-id"
    assert saved_fnos["trans_share_dir"] == "/updated-transfer"
    assert saved_fnos["download_dir"] == "/updated-nas"
    assert saved_fnos["future_setting"] == {"keep": True}
    saved_seven_zip = json.loads(paths.seven_zip_config_path.read_text(encoding="utf-8"))
    assert saved_seven_zip["7z_path"] == "thirdtool/7-Zip/7z.exe"
    assert saved_seven_zip["future_setting"] == {"keep": True}
    assert saved.fnos_config is not None
    assert saved.fnos_config.credential.cookie == "opaque-cookie"


def test_vtb_list_store_saves_name_keys_and_project_relative_paths(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    store = VtbListConfigStore(paths.vtb_list_config_path, project_root=tmp_path)
    saved = store.save(
        VtbListConfig(
            (
                VtbListItem(
                    name="新名字",
                    url="https://example.test/new",
                    archive_file_path=str(tmp_path / ".data/archive/new.txt"),
                    save_dir_path=str(tmp_path / ".data/save/new"),
                    tag_name="旧名字",
                    extra_fields={"future_setting": 7},
                ),
            )
        )
    )

    payload = json.loads(paths.vtb_list_config_path.read_text(encoding="utf-8"))
    assert list(payload) == ["新名字"]
    assert payload["新名字"] == {
        "future_setting": 7,
        "name": "新名字",
        "url": "https://example.test/new",
        "archive_file_path": ".data/archive/new.txt",
        "save_dir_path": ".data/save/new",
    }
    assert saved.items[0].tag_name == "新名字"
    assert store.load().items[0].extra_fields == {"future_setting": 7}


def test_vtb_list_store_rejects_duplicate_or_incomplete_items(tmp_path: Path) -> None:
    store = VtbListConfigStore(tmp_path / "config/vtb_list.json", project_root=tmp_path)
    duplicate = VtbListItem("same", "https://example.test", "archive.txt", "save")

    with pytest.raises(ValueError, match="不能重复"):
        store.save(VtbListConfig((duplicate, duplicate)))
    with pytest.raises(ValueError, match="链接不能为空"):
        store.save(VtbListConfig((VtbListItem("name", "", "archive.txt", "save"),)))


def test_vtb_list_store_atomic_write_keeps_previous_file_on_replace_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = VtbListConfigStore(tmp_path / "config/vtb_list.json", project_root=tmp_path)
    before = VtbListItem("before", "https://before.test", "before.txt", "before")
    store.save(VtbListConfig((before,)))
    previous_payload = store.config_path.read_text(encoding="utf-8")

    def fail_replace(self: Path, _: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    after = VtbListItem("after", "https://after.test", "after.txt", "after")
    with pytest.raises(OSError, match="replace failed"):
        store.save(VtbListConfig((after,)))

    assert store.config_path.read_text(encoding="utf-8") == previous_payload
    assert list(store.config_path.parent.glob(f".{store.config_path.name}.*.tmp")) == []


def test_fnos_store_preserves_hidden_and_unknown_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config/fnos_baidu_netdisk.json"
    write_json(
        config_path,
        {
            "base_url": "http://fnos.test",
            "username": "user",
            "password": "password",
            "cookie": "opaque-cookie",
            "verify_ssl": False,
            "language": "zh-CN",
            "appid": "app-id",
            "product": "netdisk",
            "device_id": "device-id",
            "trans_share_dir": "/transfer",
            "download_dir": "/nas",
            "request_timeout": 30,
        },
    )

    store = FnosCredentialStore(config_path)
    updated = store.update_visible_fields(
        base_url=" http://fnos.test/ ",
        username=" new-user ",
        password=" new-password ",
    )
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    assert updated.base_url == "http://fnos.test/"
    assert updated.username == "new-user"
    assert updated.password == "new-password"
    assert updated.cookie == "opaque-cookie"
    assert updated.device_id == "device-id"
    assert payload["request_timeout"] == 30
    assert payload["trans_share_dir"] == "/transfer"
    assert payload["download_dir"] == "/nas"


def test_fnos_store_atomic_write_keeps_previous_file_on_replace_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config/fnos_baidu_netdisk.json"
    store = FnosConfigStore(config_path)
    store.save(
        FnosConfig(
            credential=FnosCredential(base_url="http://before.test", cookie="opaque-cookie"),
            transfer_root_dir="/transfer",
            nas_download_dir="/nas",
        )
    )
    previous_payload = config_path.read_text(encoding="utf-8")

    def fail_replace(self: Path, _: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        store.save(FnosConfig(credential=FnosCredential(base_url="http://after.test")))

    assert config_path.read_text(encoding="utf-8") == previous_payload
    assert list(config_path.parent.glob(f".{config_path.name}.*.tmp")) == []


def test_seven_zip_store_missing_path_stays_unset(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    store = SevenZipConfigStore(paths.seven_zip_config_path, project_root=tmp_path)

    assert store.load().executable_path is None


def test_seven_zip_store_preserves_unknown_fields_and_project_relative_path(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    write_json(paths.seven_zip_config_path, {"future_setting": {"keep": True}})
    store = SevenZipConfigStore(paths.seven_zip_config_path, project_root=tmp_path)

    store.save(
        SevenZipConfig(
            executable_path=tmp_path / "thirdtool/7-Zip/7z.exe",
            default_password="archive-password",
        )
    )

    payload = json.loads(paths.seven_zip_config_path.read_text(encoding="utf-8"))
    assert payload["7z_path"] == "thirdtool/7-Zip/7z.exe"
    assert payload["decompress_password"] == "archive-password"
    assert payload["future_setting"] == {"keep": True}
    assert store.load().executable_path == tmp_path / "thirdtool/7-Zip/7z.exe"


def test_core_config_managers_are_independent_and_resolve_from_project_root(tmp_path: Path) -> None:
    first_path = tmp_path / "config/first.json"
    second_path = tmp_path / "config/second.json"
    write_json(
        first_path,
        {
            "login_info": {
                "url": "https://first.test/login",
                "username": "first",
                "password": "password",
                "storage_state": {"cookies": []},
            },
            "resource_link_markers": ["https://first.test/resource"],
            "log_dir": ".data/first-logs",
        },
    )
    write_json(
        second_path,
        {
            "login_info": {
                "url": "https://second.test/login",
                "username": "second",
                "password": "password",
                "storage_state": {"cookies": []},
            },
            "resource_link_markers": ["https://second.test/resource"],
            "log_dir": ".data/second-logs",
        },
    )

    first = ConfigManager(first_path, project_root=tmp_path)
    second = ConfigManager(second_path, project_root=tmp_path)

    assert first is not second
    assert first.get_site_origin() == "https://first.test"
    assert first.get_resource_link_markers() == ("https://first.test/resource",)
    assert second.get_site_origin() == "https://second.test"
    assert second.get_log_dir_path() == tmp_path / ".data/second-logs"

    vtb_path = tmp_path / "config/vtb_list.json"
    write_json(
        vtb_path,
        {
            "tag": {
                "name": "Tag",
                "url": "https://example.test/tag",
                "archive_file_path": ".data/archive/tag.txt",
                "save_dir_path": ".data/save/tag",
            }
        },
    )
    vtb_config = VtbConfigManager(vtb_path, project_root=tmp_path).get_vtb_config("tag")
    assert vtb_config.archive_file_path == tmp_path / ".data/archive/tag.txt"
    assert vtb_config.save_dir_path == tmp_path / ".data/save/tag"


def test_app_config_is_only_a_runtime_aggregate() -> None:
    assert set(AppConfig.__dataclass_fields__) == {
        "spider_base_config",
        "vtb_list_config",
        "fnos_config",
        "seven_zip_config",
    }
    assert AppConfig.empty() == AppConfig()