from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

SEMVER_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)$"
)


def project_version(pyproject_path: Path) -> str:
    with pyproject_path.open("rb") as pyproject_file:
        payload = tomllib.load(pyproject_file)
    version = str(payload.get("project", {}).get("version", "")).strip()
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(
            "[project].version must use Semantic Versioning: MAJOR.MINOR.PATCH"
        )
    return version


def numeric_version(version: str) -> tuple[int, int, int, int]:
    match = SEMVER_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"Invalid semantic version: {version}")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        0,
    )


def write_windows_version_file(version: str, target_path: Path) -> None:
    version_tuple = numeric_version(version)
    dotted_numeric_version = ".".join(str(part) for part in version_tuple)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        "\n".join(
            [
                "VSVersionInfo(",
                f"  ffi=FixedFileInfo(filevers={version_tuple}, prodvers={version_tuple}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),",
                "  kids=[",
                "    StringFileInfo([",
                "      StringTable('040904B0', [",
                "        StringStruct('CompanyName', 'vtb-asmr-tool'),",
                "        StringStruct('FileDescription', 'VTB ASMR Tool GUI'),",
                f"        StringStruct('FileVersion', '{version}'),",
                "        StringStruct('InternalName', 'vtb_asmr_tool_gui'),",
                "        StringStruct('OriginalFilename', 'vtb_asmr_tool_gui.exe'),",
                "        StringStruct('ProductName', 'VTB ASMR Tool GUI'),",
                f"        StringStruct('ProductVersion', '{version}'),",
                f"        StringStruct('Comments', 'Semantic Version {version}; numeric file version {dotted_numeric_version}')",
                "      ])",
                "    ]),",
                "    VarFileInfo([VarStruct('Translation', [1033, 1200])])",
                "  ]",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )


def stage_playwright_browsers(target_dir: Path) -> None:
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    try:
        chromium_executable = Path(playwright.chromium.executable_path)
    finally:
        playwright.stop()

    cache_root = chromium_executable.parents[2]
    chromium_revision = chromium_executable.parents[1].name.removeprefix("chromium-")
    registry_path = (
        Path(sys.executable).resolve().parent
        / "Lib/site-packages/playwright/driver/package/browsers.json"
    )
    if not registry_path.is_file():
        import playwright

        registry_path = (
            Path(playwright.__file__).resolve().parent
            / "driver/package/browsers.json"
        )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    revisions = {
        str(item["name"]): str(item["revision"])
        for item in registry["browsers"]
        if item["name"] in {"chromium", "chromium-headless-shell", "ffmpeg", "winldd"}
    }
    if revisions.get("chromium") != chromium_revision:
        raise RuntimeError("Playwright Chromium cache does not match the installed package")

    required_dirs = [
        cache_root / f"chromium-{chromium_revision}",
        cache_root / f"chromium_headless_shell-{revisions['chromium-headless-shell']}",
    ]
    optional_dirs = [
        cache_root / f"ffmpeg-{revisions['ffmpeg']}",
        cache_root / f"winldd-{revisions['winldd']}",
    ]
    missing = [str(path) for path in required_dirs if not path.is_dir()]
    if missing:
        raise FileNotFoundError(
            "Playwright browser components are missing. Run "
            "`python -m playwright install chromium` before building."
        )

    shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_dir in [*required_dirs, *optional_dirs]:
        if source_dir.is_dir():
            shutil.copytree(
                source_dir,
                target_dir / source_dir.name,
                ignore=shutil.ignore_patterns("debug.log"),
            )


def create_package_archive(source_dir: Path, target_path: Path) -> None:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Package staging directory does not exist: {source_dir}")

    package_files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    if not package_files:
        raise ValueError("Package staging directory is empty")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.unlink(missing_ok=True)
    with ZipFile(
        target_path,
        mode="w",
        compression=ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        for source_path in package_files:
            archive.write(source_path, source_path.relative_to(source_dir).as_posix())

    with ZipFile(target_path, mode="r") as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise RuntimeError(f"ZIP integrity check failed: {corrupt_member}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Windows build metadata")
    subparsers = parser.add_subparsers(dest="command", required=True)

    version_parser = subparsers.add_parser("version")
    version_parser.add_argument("pyproject", type=Path)
    version_parser.add_argument("--output", type=Path)

    resource_parser = subparsers.add_parser("write-version-file")
    resource_parser.add_argument("pyproject", type=Path)
    resource_parser.add_argument("target", type=Path)

    browser_parser = subparsers.add_parser("stage-playwright")
    browser_parser.add_argument("target", type=Path)

    archive_parser = subparsers.add_parser("create-archive")
    archive_parser.add_argument("source", type=Path)
    archive_parser.add_argument("target", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "version":
        version = project_version(args.pyproject)
        if args.output is None:
            print(version)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(version, encoding="ascii")
    elif args.command == "write-version-file":
        write_windows_version_file(project_version(args.pyproject), args.target)
    elif args.command == "stage-playwright":
        stage_playwright_browsers(args.target)
    elif args.command == "create-archive":
        create_package_archive(args.source, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())