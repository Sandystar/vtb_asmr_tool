from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from spider_vtbasmr_gui.config import AppConfig
from spider_vtbasmr_gui.config.seven_zip_config import SevenZipConfig
from spider_vtbasmr_gui.services.archive_probe import SevenZipArchiveProbe
from spider_vtbasmr_gui.services.decompression_service import DecompressionService


class FakeArchiveProbe:
    def __init__(self, formats: dict[str, str]) -> None:
        self._formats = formats

    def detect_format(self, path: Path) -> str | None:
        return self._formats.get(path.name)


def build_service(
    tmp_path: Path,
    formats: dict[str, str],
) -> tuple[DecompressionService, Path]:
    seven_zip = tmp_path / "7z.exe"
    seven_zip.touch()
    context = SimpleNamespace(
        app_config=AppConfig(
            seven_zip_config=SevenZipConfig(
                executable_path=seven_zip,
                default_password="default-password",
            )
        )
    )
    provider = SimpleNamespace(require=lambda: context)
    service = DecompressionService(
        provider,  # type: ignore[arg-type]
        probe_factory=lambda _seven_zip, _password: FakeArchiveProbe(formats),
    )
    return service, seven_zip


def test_seven_zip_probe_detects_format_without_using_filename_suffix(tmp_path: Path) -> None:
    source = tmp_path / "archive-without-extension"
    source.touch()
    calls: list[tuple[list[str], dict[str, object]]] = []

    def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "Path = archive\nType = 7z\n", "")

    probe = SevenZipArchiveProbe(
        tmp_path / "7z.exe",
        password="password",
        runner=runner,
    )

    assert probe.detect_format(source) == "7z"
    command, kwargs = calls[0]
    assert command[-2:] == [str(source), "-ppassword"]
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["timeout"] == 30


def test_seven_zip_probe_rejects_file_when_7zip_reports_no_type(tmp_path: Path) -> None:
    source = tmp_path / "video.mp4"
    source.touch()

    def runner(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 2, "", "ERROR: Is not archive")

    probe = SevenZipArchiveProbe(tmp_path / "7z.exe", runner=runner)

    assert probe.detect_format(source) is None


def test_discover_uses_content_and_prefers_outer_archive_over_stale_temp(tmp_path: Path) -> None:
    service, _ = build_service(
        tmp_path,
        {
            "package-without-extension": "tar",
            "rzy260718.7z严禁网盘内解压": "7z",
        },
    )
    source = tmp_path / "source"
    date_dir = source / "Tag" / "5950" / "2026-07-20"
    temp_dir = date_dir / "temp"
    temp_dir.mkdir(parents=True)
    outer = date_dir / "package-without-extension"
    outer.touch()
    (temp_dir / "rzy260718.7z严禁网盘内解压").touch()
    (date_dir / "video.mp4").touch()

    files = service.discover(source, tmp_path / "target")

    assert [item.source_file_path for item in files] == [outer]


def test_decompress_detects_and_extracts_nested_archive_with_trailing_text(
    tmp_path: Path,
    monkeypatch,
) -> None:
    nested_name = "rzy260718.7z严禁网盘内解压"
    service, seven_zip = build_service(
        tmp_path,
        {
            "outer-container": "tar",
            nested_name: "7z",
        },
    )
    source = tmp_path / "source"
    date_dir = source / "Tag" / "5950" / "2026-07-20"
    date_dir.mkdir(parents=True)
    outer = date_dir / "outer-container"
    outer.touch()
    target = tmp_path / "target"
    calls: list[tuple[Path, Path, str | None]] = []

    def fake_extract(
        received_seven_zip: Path,
        archive: Path,
        output: Path,
        password: str | None,
    ) -> None:
        assert received_seven_zip == seven_zip
        output.mkdir(parents=True, exist_ok=True)
        calls.append((archive, output, password))
        if archive == outer:
            (output / nested_name).touch()
        else:
            (output / "video.mp4").touch()

    monkeypatch.setattr(service, "_extract", fake_extract)

    result = service.decompress(source, target)

    assert result.processed_count == 1
    assert [archive.name for archive, _, _ in calls] == ["outer-container", nested_name]
    assert calls[1][1] == target / "Tag" / "2026" / "07" / "2026.07.20"
    assert (calls[1][1] / "video.mp4").is_file()