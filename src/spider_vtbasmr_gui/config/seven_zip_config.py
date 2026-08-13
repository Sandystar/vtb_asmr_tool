from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping


@dataclass(frozen=True, slots=True)
class SevenZipConfig:
    executable_path: Path | None = None
    default_password: str | None = None

    def has_executable(self) -> bool:
        return self.executable_path is not None


class SevenZipConfigStore:
    def __init__(self, config_path: Path, *, project_root: Path) -> None:
        self._config_path = config_path.expanduser().resolve(strict=False)
        self._project_root = project_root.expanduser().resolve(strict=False)

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> SevenZipConfig:
        payload = self._load_payload()
        return SevenZipConfig(
            executable_path=self._resolve_path(payload.get("7z_path")),
            default_password=self._text(payload.get("decompress_password")),
        )

    def save(self, config: SevenZipConfig) -> None:
        payload = self._load_payload()
        payload.update(
            {
                "7z_path": self._portable_path(config.executable_path),
                "decompress_password": self._text(config.default_password),
            }
        )
        self._atomic_write(payload)

    def update_visible_fields(
        self,
        *,
        executable_path: Path | None,
        default_password: str | None,
    ) -> SevenZipConfig:
        updated = replace(
            self.load(),
            executable_path=self._resolved_optional_path(executable_path),
            default_password=self._text(default_password),
        )
        self.save(updated)
        return updated

    def _load_payload(self) -> dict[str, object]:
        if not self._config_path.exists():
            return {}
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"7zip 配置必须是 JSON object: {self._config_path}")
        return dict(payload)

    def _resolve_path(self, value: object) -> Path | None:
        text = self._text(value)
        if text is None:
            return None
        return self._resolved_optional_path(Path(text))

    def _resolved_optional_path(self, path: Path | None) -> Path | None:
        if path is None:
            return None
        expanded = path.expanduser()
        if expanded.is_absolute():
            return expanded.resolve(strict=False)
        return (self._project_root / expanded).resolve(strict=False)

    def _portable_path(self, path: Path | None) -> str | None:
        resolved = self._resolved_optional_path(path)
        if resolved is None:
            return None
        try:
            return resolved.relative_to(self._project_root).as_posix()
        except ValueError:
            return str(resolved)

    def _atomic_write(self, payload: Mapping[str, object]) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._config_path.parent,
                prefix=f".{self._config_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(json.dumps(payload, ensure_ascii=False, indent=2))
                temporary_file.write("\n")
                temporary_path = Path(temporary_file.name)
            temporary_path.replace(self._config_path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None