from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from spider_vtbasmr_gui.services.archive_probe import ArchiveProbe, SevenZipArchiveProbe
from spider_vtbasmr_gui.services.runtime_context import RuntimeContextProvider


@dataclass(frozen=True, slots=True)
class DiscoveredArchiveFile:
    tag_name: str
    content_id: str
    published_date: str
    source_file_path: Path
    temp_output_dir: Path
    final_output_dir: Path


@dataclass(frozen=True, slots=True)
class DecompressionPreviewResult:
    files: list[DiscoveredArchiveFile]
    summary_text: str


@dataclass(frozen=True, slots=True)
class DecompressionResult:
    processed_count: int
    summary_text: str


class DecompressionService:
    _DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def __init__(
        self,
        context_provider: RuntimeContextProvider,
        *,
        probe_factory: Callable[[Path, str | None], ArchiveProbe] | None = None,
    ) -> None:
        self._context_provider = context_provider
        self._probe_factory = probe_factory or self._build_probe

    def preview(self, source_root: str | Path, target_root: str | Path) -> DecompressionPreviewResult:
        files = self.discover(source_root, target_root)
        return DecompressionPreviewResult(
            files=files,
            summary_text=f"预览完成，共发现 {len(files)} 个待解压文件。",
        )

    def discover(self, source_root: str | Path, target_root: str | Path) -> list[DiscoveredArchiveFile]:
        source = Path(source_root).expanduser().resolve(strict=False)
        target = Path(target_root).expanduser().resolve(strict=False)
        if not source.is_dir():
            raise FileNotFoundError(f"源目录不存在: {source}")
        probe = self._create_probe()
        candidates = [
            path
            for path in source.rglob("*")
            if path.is_file() and probe.detect_format(path) is not None
        ]
        seeds = self._select_seed_archives(source, candidates)
        return [self._describe(source, target, path) for path in seeds]

    def decompress(
        self,
        source_root: str | Path,
        target_root: str | Path,
        password: str | None = None,
    ) -> DecompressionResult:
        files = self.discover(source_root, target_root)
        seven_zip = self._require_seven_zip_path()
        seven_zip_config = self._context_provider.require().app_config.seven_zip_config
        resolved_password = (
            password or (seven_zip_config.default_password if seven_zip_config else None) or ""
        ).strip() or None
        probe = self._probe_factory(seven_zip, resolved_password)
        for item in files:
            self._extract(seven_zip, item.source_file_path, item.temp_output_dir, resolved_password)
            nested = [
                path
                for path in item.temp_output_dir.rglob("*")
                if path.is_file()
                and path.resolve(strict=False) != item.source_file_path.resolve(strict=False)
                and probe.detect_format(path) is not None
            ]
            if nested:
                for archive_path in nested:
                    self._extract(seven_zip, archive_path, item.final_output_dir, resolved_password)
            else:
                self._extract(seven_zip, item.source_file_path, item.final_output_dir, resolved_password)
        return DecompressionResult(
            processed_count=len(files),
            summary_text=f"解压完成，共处理 {len(files)} 个压缩文件。",
        )

    def _create_probe(self) -> ArchiveProbe:
        config = self._context_provider.require().app_config.seven_zip_config
        password = (config.default_password if config else None) or None
        return self._probe_factory(self._require_seven_zip_path(), password)

    def _require_seven_zip_path(self) -> Path:
        config = self._context_provider.require().app_config.seven_zip_config
        seven_zip = config.executable_path if config else None
        if seven_zip is None or not seven_zip.is_file():
            raise FileNotFoundError(f"7z 可执行文件不存在: {seven_zip}")
        return seven_zip

    @staticmethod
    def _build_probe(seven_zip_path: Path, password: str | None) -> ArchiveProbe:
        return SevenZipArchiveProbe(seven_zip_path, password=password)

    @classmethod
    def _select_seed_archives(cls, source: Path, candidates: list[Path]) -> list[Path]:
        grouped: dict[Path, list[Path]] = {}
        for path in candidates:
            date_dir = cls._find_date_directory(source, path)
            if date_dir is not None:
                grouped.setdefault(date_dir, []).append(path)

        selected: list[Path] = []
        for date_dir, paths in grouped.items():
            generated_temp = date_dir / "temp"
            outside_temp = [path for path in paths if generated_temp not in path.parents]
            selected.extend(outside_temp or paths)
        return sorted(set(selected))

    @classmethod
    def _find_date_directory(cls, source: Path, path: Path) -> Path | None:
        return next(
            (
                parent
                for parent in path.parents
                if parent != source and cls._DATE_PATTERN.match(parent.name)
            ),
            None,
        )

    def _describe(self, source: Path, target: Path, path: Path) -> DiscoveredArchiveFile:
        date_dir = next(
            (parent for parent in path.parents if parent != source and self._DATE_PATTERN.match(parent.name)),
            None,
        )
        if date_dir is None or len(date_dir.relative_to(source).parts) < 3:
            raise ValueError(f"压缩文件路径缺少 Tag、内容 ID 或发布日期层级: {path}")
        content_dir = date_dir.parent
        tag_dir = content_dir.parent
        year, month, day = date_dir.name.split("-")
        return DiscoveredArchiveFile(
            tag_name=tag_dir.name,
            content_id=content_dir.name,
            published_date=date_dir.name,
            source_file_path=path,
            temp_output_dir=date_dir / "temp",
            final_output_dir=target / tag_dir.name / year / month / f"{year}.{month}.{day}",
        )

    @staticmethod
    def _extract(seven_zip: Path, source: Path, target: Path, password: str | None) -> None:
        target.mkdir(parents=True, exist_ok=True)
        command = [str(seven_zip), "x", "-y", str(source), f"-o{target}"]
        if password:
            command.append(f"-p{password}")
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
            raise RuntimeError(f"7z 解压失败: {source}; {detail}")