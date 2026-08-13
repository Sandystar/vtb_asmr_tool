from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from tools.windows_build import (
    create_package_archive,
    numeric_version,
    project_version,
    write_windows_version_file,
)


def test_project_version_uses_semver_from_pyproject(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        '[project]\nname = "example"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )

    assert project_version(pyproject_path) == "1.2.3"
    assert numeric_version("1.2.3") == (1, 2, 3, 0)


def test_project_version_rejects_non_semver(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        '[project]\nname = "example"\nversion = "1.2"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Semantic Versioning"):
        project_version(pyproject_path)


def test_windows_version_file_contains_project_version(tmp_path: Path) -> None:
    version_file = tmp_path / "version_info.txt"

    write_windows_version_file("2.4.6", version_file)

    content = version_file.read_text(encoding="utf-8")
    assert "filevers=(2, 4, 6, 0)" in content
    assert "StringStruct('FileVersion', '2.4.6')" in content
    assert "StringStruct('ProductVersion', '2.4.6')" in content


def test_create_package_archive_uses_staging_contents_as_zip_root(
    tmp_path: Path,
) -> None:
    package_dir = tmp_path / "package"
    (package_dir / "config").mkdir(parents=True)
    (package_dir / "thirdtool/7-Zip").mkdir(parents=True)
    (package_dir / "vtb_asmr_tool_gui_v1.2.3.exe").write_bytes(b"exe")
    (package_dir / "config/vtbasmr_base.json").write_text("{}", encoding="utf-8")
    (package_dir / "thirdtool/7-Zip/7z.exe").write_bytes(b"7z")
    archive_path = tmp_path / "publish/vtb_asmr_tool_gui_v1.2.3.zip"

    create_package_archive(package_dir, archive_path)

    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {
            "config/vtbasmr_base.json",
            "thirdtool/7-Zip/7z.exe",
            "vtb_asmr_tool_gui_v1.2.3.exe",
        }
