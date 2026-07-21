from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


_ROOT_FILES = ("Local State", "Last Version", "First Run")
_PROFILE_ENTRIES = (
    "Preferences",
    "Secure Preferences",
    "Cookies",
    "Network",
    "Local Storage",
    "Session Storage",
    "IndexedDB",
    "WebStorage",
    "Service Worker",
)
_LOCK_FILE_NAMES = {"LOCK", "SingletonCookie", "SingletonLock", "SingletonSocket"}


@dataclass(slots=True)
class BrowserProfileSnapshot:
    temporary_directory: TemporaryDirectory[str]
    user_data_dir: Path
    profile_directory: str

    def cleanup(self) -> None:
        self.temporary_directory.cleanup()


def create_browser_profile_snapshot(
    user_data_dir: str | Path,
    profile_directory: str = "Default",
) -> BrowserProfileSnapshot:
    source_root = Path(user_data_dir).expanduser().resolve(strict=False)
    source_profile = source_root / profile_directory
    if not source_root.is_dir():
        raise FileNotFoundError(f"Browser user data directory not found: {source_root}")
    if not source_profile.is_dir():
        raise FileNotFoundError(f"Browser profile directory not found: {source_profile}")

    temporary_directory = TemporaryDirectory(prefix="vtb-asmr-browser-profile-")
    snapshot_root = Path(temporary_directory.name) / "User Data"
    snapshot_profile = snapshot_root / profile_directory
    snapshot_profile.mkdir(parents=True, exist_ok=True)

    try:
        for file_name in _ROOT_FILES:
            _copy_available_path(source_root / file_name, snapshot_root / file_name)
        for entry_name in _PROFILE_ENTRIES:
            _copy_available_path(
                source_profile / entry_name,
                snapshot_profile / entry_name,
            )
    except Exception:
        temporary_directory.cleanup()
        raise

    return BrowserProfileSnapshot(
        temporary_directory=temporary_directory,
        user_data_dir=snapshot_root,
        profile_directory=profile_directory,
    )


def _copy_available_path(source: Path, destination: Path) -> None:
    if not source.exists() or source.name in _LOCK_FILE_NAMES:
        return
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, destination)
        except OSError:
            return
        return
    if not source.is_dir():
        return

    destination.mkdir(parents=True, exist_ok=True)
    try:
        children = tuple(source.iterdir())
    except OSError:
        return
    for child in children:
        _copy_available_path(child, destination / child.name)