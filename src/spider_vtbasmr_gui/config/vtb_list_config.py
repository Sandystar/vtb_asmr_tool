from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping


_REQUIRED_FIELDS = ("name", "url", "archive_file_path", "save_dir_path")


@dataclass(frozen=True, slots=True)
class VtbListItem:
    name: str
    url: str
    archive_file_path: str
    save_dir_path: str
    tag_name: str | None = None
    extra_fields: dict[str, object] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return (self.tag_name or self.name).strip()


@dataclass(frozen=True, slots=True)
class VtbListConfig:
    items: tuple[VtbListItem, ...] = ()


class VtbListConfigStore:
    def __init__(self, config_path: Path, *, project_root: Path) -> None:
        self._config_path = config_path.expanduser().resolve(strict=False)
        self._project_root = project_root.expanduser().resolve(strict=False)

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> VtbListConfig:
        payload = self._load_payload()
        items: list[VtbListItem] = []
        for tag_name, raw_item in payload.items():
            if not isinstance(raw_item, dict):
                raise ValueError(f"VTB 列表条目必须是 JSON object: {tag_name}")
            items.append(self._build_item(str(tag_name), raw_item))
        return VtbListConfig(tuple(items))

    def save(self, config: VtbListConfig) -> VtbListConfig:
        normalized = self._normalize(config)
        current_payload = self._load_payload()
        payload: dict[str, object] = {}
        for item in normalized.items:
            current_item = current_payload.get(item.key)
            raw_item = dict(current_item) if isinstance(current_item, dict) else {}
            raw_item.update(deepcopy(item.extra_fields))
            raw_item.update(
                {
                    "name": item.name,
                    "url": item.url,
                    "archive_file_path": item.archive_file_path,
                    "save_dir_path": item.save_dir_path,
                }
            )
            payload[item.key] = raw_item
        self._atomic_write(payload)
        return normalized

    def _normalize(self, config: VtbListConfig) -> VtbListConfig:
        items: list[VtbListItem] = []
        used_keys: set[str] = set()
        for index, item in enumerate(config.items, start=1):
            name = self._required_text(item.name, "名字", index)
            tag_name = name
            if tag_name in used_keys:
                raise ValueError(f"抓取列表中的名字不能重复：{tag_name}")
            used_keys.add(tag_name)
            items.append(
                VtbListItem(
                    name=name,
                    url=self._required_text(item.url, "链接", index),
                    archive_file_path=self._portable_path_text(
                        self._required_text(item.archive_file_path, "归档记录文件", index)
                    ),
                    save_dir_path=self._portable_path_text(
                        self._required_text(item.save_dir_path, "保存文件夹", index)
                    ),
                    tag_name=tag_name,
                    extra_fields=deepcopy(item.extra_fields),
                )
            )
        return VtbListConfig(tuple(items))

    def _load_payload(self) -> dict[str, object]:
        if not self._config_path.exists():
            return {}
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"VTB 列表配置必须是 JSON object: {self._config_path}")
        return dict(payload)

    def _build_item(self, tag_name: str, payload: Mapping[str, object]) -> VtbListItem:
        fields = {
            field_name: self._required_payload_text(payload, field_name, tag_name)
            for field_name in _REQUIRED_FIELDS
        }
        return VtbListItem(
            name=fields["name"],
            url=fields["url"],
            archive_file_path=fields["archive_file_path"],
            save_dir_path=fields["save_dir_path"],
            tag_name=tag_name,
            extra_fields={
                key: deepcopy(value)
                for key, value in payload.items()
                if key not in _REQUIRED_FIELDS
            },
        )

    def _portable_path_text(self, value: str) -> str:
        path = Path(value).expanduser()
        if not path.is_absolute():
            return path.as_posix()
        resolved = path.resolve(strict=False)
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
    def _required_payload_text(
        payload: Mapping[str, object],
        field_name: str,
        tag_name: str,
    ) -> str:
        value = payload.get(field_name)
        text = str(value).strip() if value is not None else ""
        if not text:
            raise ValueError(f"VTB 列表条目 {tag_name} 缺少字段：{field_name}")
        return text

    @staticmethod
    def _required_text(value: object, label: str, index: int) -> str:
        text = str(value).strip() if value is not None else ""
        if not text:
            raise ValueError(f"抓取列表第 {index} 项的{label}不能为空")
        return text