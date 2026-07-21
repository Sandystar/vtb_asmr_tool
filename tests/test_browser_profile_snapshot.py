from __future__ import annotations

from pathlib import Path

import pytest

from spider_vtbasmr.browser.profile_snapshot import create_browser_profile_snapshot


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_profile_snapshot_copies_auth_state_without_lock_files(tmp_path: Path) -> None:
    source = tmp_path / "User Data"
    write_text(source / "Local State", "root-state")
    write_text(source / "Default/Network/Cookies", "cookie-state")
    write_text(source / "Default/Local Storage/leveldb/data", "local-state")
    write_text(source / "Default/Network/LOCK", "locked")

    snapshot = create_browser_profile_snapshot(source)
    snapshot_root = snapshot.user_data_dir
    try:
        assert (snapshot_root / "Local State").read_text(encoding="utf-8") == "root-state"
        assert (snapshot_root / "Default/Network/Cookies").read_text(encoding="utf-8") == "cookie-state"
        assert (snapshot_root / "Default/Local Storage/leveldb/data").read_text(encoding="utf-8") == "local-state"
        assert not (snapshot_root / "Default/Network/LOCK").exists()
    finally:
        snapshot.cleanup()

    assert not snapshot_root.exists()


def test_profile_snapshot_requires_existing_profile(tmp_path: Path) -> None:
    source = tmp_path / "User Data"
    source.mkdir()

    with pytest.raises(FileNotFoundError, match="profile directory"):
        create_browser_profile_snapshot(source, "Profile 9")
