from __future__ import annotations

import json
from pathlib import Path

from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager
from spider_vtbasmr_gui.config import AppConfig, AppConfigManager
from spider_vtbasmr_gui.project_paths import ProjectPaths


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_app_config_round_trip_uses_project_relative_paths(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    manager = AppConfigManager(project_paths=paths)
    config_files = [
        tmp_path / ".data/.config/base.json",
        tmp_path / ".data/.config/vtb.json",
        tmp_path / ".data/.config/fnos.json",
    ]
    for path in config_files:
        write_json(path, {})

    saved = manager.save(
        AppConfig(
            spider_base_config_path=config_files[0],
            spider_vtb_config_path=config_files[1],
            netdisk_config_path=config_files[2],
            seven_zip_path=tmp_path / "tools/7z.exe",
        )
    )

    raw_payload = json.loads(paths.app_config_path.read_text(encoding="utf-8"))
    assert not Path(raw_payload["spider_base_config_path"]).is_absolute()
    assert saved.spider_base_config_path == config_files[0]
    assert manager.load().netdisk_config_path == config_files[2]
    assert "compress_suffix_list" not in raw_payload


def test_core_config_managers_are_independent_and_resolve_from_project_root(tmp_path: Path) -> None:
    first_path = tmp_path / "config/first.json"
    second_path = tmp_path / "config/second.json"
    write_json(
        first_path,
        {
            "browser": {
                "channel": "msedge",
                "user_data_dir": ".data/browser-profile",
                "profile_directory": "Profile 2",
                "use_existing_profile": True,
            },
            "login_info": {"state_file_path": ".data/first-state"},
            "log_dir": ".data/first-logs",
        },
    )
    write_json(
        second_path,
        {
            "browser": {"channel": "chrome"},
            "login_info": {"state_file_path": ".data/second-state"},
            "log_dir": ".data/second-logs",
        },
    )

    first = ConfigManager(first_path, project_root=tmp_path)
    second = ConfigManager(second_path, project_root=tmp_path)

    assert first is not second
    assert first.get_browser_channel() == "msedge"
    assert first.get_browser_user_data_dir() == tmp_path / ".data/browser-profile"
    assert first.get_browser_profile_directory() == "Profile 2"
    assert first.use_existing_browser_profile() is True
    assert second.get_browser_channel() == "chrome"
    assert second.get_log_dir_path() == tmp_path / ".data/second-logs"

    vtb_path = tmp_path / "config/vtb.json"
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