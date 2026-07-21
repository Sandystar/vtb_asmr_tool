from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class FnosCredential:
    base_url: str | None = None
    username: str | None = None
    password: str | None = None
    cookie: str | None = None
    user_agent: str | None = None
    verify_ssl: bool = True
    language: str = "zh-CN"
    appid: str = "116623829"
    product: str = "netdisk"
    device_id: str | None = None
    browser_type: str = "edge"
    browser_user_data_dir: str | None = None
    browser_profile_directory: str = "Default"
    use_existing_browser_profile: bool = True

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "FnosCredential":
        field_names = {field.name for field in fields(cls)}
        values = {key: value for key, value in payload.items() if key in field_names}
        if "browser_user_data_dir" not in values:
            for alias in ("user_data_dir", "browser_data_dir"):
                if payload.get(alias):
                    values["browser_user_data_dir"] = payload[alias]
                    break
        if "browser_profile_directory" not in values and payload.get("profile_directory"):
            values["browser_profile_directory"] = payload["profile_directory"]
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


class FnosCredentialStore:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path.expanduser().resolve(strict=False)

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> FnosCredential:
        if not self._config_path.exists():
            return FnosCredential()
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"FNOS 配置必须是 JSON object: {self._config_path}")
        return FnosCredential.from_mapping(payload)

    def save(self, credential: FnosCredential) -> None:
        existing_payload: dict[str, object] = {}
        if self._config_path.exists():
            loaded_payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
            if isinstance(loaded_payload, dict):
                existing_payload = loaded_payload
        existing_payload.update(credential.to_dict())
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(existing_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )