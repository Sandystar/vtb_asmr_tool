from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping


@dataclass(frozen=True, slots=True)
class FnosCredential:
    base_url: str | None = None
    username: str | None = None
    password: str | None = None
    cookie: str | None = None
    verify_ssl: bool = True
    language: str = "zh-CN"
    appid: str = "116623829"
    product: str = "netdisk"
    device_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "FnosCredential":
        field_names = {field.name for field in fields(cls)}
        values = {key: value for key, value in payload.items() if key in field_names}
        return cls(**values)

    def require_api_access(self) -> None:
        missing = [
            label
            for label, value in [
                ("base_url", self.base_url),
                ("cookie", self.cookie),
                ("device_id", self.device_id),
            ]
            if not value
        ]
        if missing:
            raise ValueError(f"FNOS 认证配置缺少字段: {', '.join(missing)}")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FnosConfig:
    credential: FnosCredential = FnosCredential()
    transfer_root_dir: str | None = None
    nas_download_dir: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "FnosConfig":
        return cls(
            credential=FnosCredential.from_mapping(payload),
            transfer_root_dir=cls._text(payload.get("trans_share_dir")),
            nas_download_dir=cls._text(payload.get("download_dir")),
        )

    def has_transfer_settings(self) -> bool:
        return bool(self.transfer_root_dir and self.nas_download_dir)

    def to_dict(self) -> dict[str, object]:
        return {
            **self.credential.to_dict(),
            "trans_share_dir": self.transfer_root_dir,
            "download_dir": self.nas_download_dir,
        }

    @staticmethod
    def _text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class FnosConfigStore:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path.expanduser().resolve(strict=False)

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> FnosConfig:
        return FnosConfig.from_mapping(self._load_payload())

    def save(self, config: FnosConfig) -> None:
        payload = self._load_payload()
        payload.update(config.to_dict())
        self._atomic_write(payload)

    def update_visible_fields(
        self,
        *,
        base_url: str | None,
        username: str | None,
        password: str | None,
        transfer_root_dir: str | None,
        nas_download_dir: str | None,
    ) -> FnosConfig:
        current = self.load()
        updated = replace(
            current,
            credential=replace(
                current.credential,
                base_url=self._text(base_url),
                username=self._text(username),
                password=self._text(password),
            ),
            transfer_root_dir=self._text(transfer_root_dir),
            nas_download_dir=self._text(nas_download_dir),
        )
        self.save(updated)
        return updated

    def _load_payload(self) -> dict[str, object]:
        if not self._config_path.exists():
            return {}
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"FNOS 配置必须是 JSON object: {self._config_path}")
        return dict(payload)

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
        return FnosConfig._text(value)


class FnosCredentialStore:
    def __init__(self, config_path: Path) -> None:
        self._config_store = FnosConfigStore(config_path)

    @property
    def config_path(self) -> Path:
        return self._config_store.config_path

    def load(self) -> FnosCredential:
        return self._config_store.load().credential

    def save(self, credential: FnosCredential) -> None:
        current = self._config_store.load()
        self._config_store.save(replace(current, credential=credential))

    def update_visible_fields(
        self,
        *,
        base_url: str | None,
        username: str | None,
        password: str | None,
    ) -> FnosCredential:
        current = self._config_store.load()
        updated = replace(
            current,
            credential=replace(
                current.credential,
                base_url=FnosConfig._text(base_url),
                username=FnosConfig._text(username),
                password=FnosConfig._text(password),
            ),
        )
        self._config_store.save(updated)
        return updated.credential
