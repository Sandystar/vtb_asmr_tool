from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True, slots=True)
class SpiderBaseConfig:
    login_url: str
    username: str
    password: str
    resource_link_markers: tuple[str, ...]
    log_dir: str
    storage_state: dict[str, object] | None = None

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        project_root: Path,
    ) -> "SpiderBaseConfig":
        del project_root
        login_info = payload.get("login_info", {})
        if not isinstance(login_info, Mapping):
            raise ValueError("login_info must be an object")

        state = login_info.get("storage_state")
        storage_state = deepcopy(dict(state)) if isinstance(state, Mapping) else None

        markers = payload.get("resource_link_markers")
        if not isinstance(markers, (list, tuple)):
            markers = []

        return cls(
            login_url=_text(login_info.get("url")),
            username=_text(login_info.get("username")),
            password=_text(login_info.get("password")),
            resource_link_markers=_normalize_markers(markers),
            log_dir=_text(payload.get("log_dir")),
            storage_state=storage_state,
        )

    @property
    def site_origin(self) -> str:
        parsed_url = urlsplit(self.login_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("login_info.url must be an absolute URL")
        return urlunsplit((parsed_url.scheme, parsed_url.netloc, "", "", ""))

    def with_storage_state(self, storage_state: Mapping[str, object]) -> "SpiderBaseConfig":
        return replace(self, storage_state=deepcopy(dict(storage_state)))


class BaseConfigStore:
    def __init__(self, config_path: Path, *, project_root: Path | None = None) -> None:
        self._config_path = config_path.expanduser().resolve(strict=False)
        self._project_root = (project_root or Path.cwd()).expanduser().resolve(strict=False)

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> SpiderBaseConfig:
        return SpiderBaseConfig.from_payload(
            self.load_payload(),
            project_root=self._project_root,
        )

    def load_payload(self) -> dict[str, object]:
        if not self._config_path.is_file():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"Config file must contain a JSON object: {self._config_path}")
        return payload

    def save(self, config: SpiderBaseConfig) -> SpiderBaseConfig:
        payload = deepcopy(self.load_payload()) if self._config_path.is_file() else {}
        login_info = payload.get("login_info", {})
        if not isinstance(login_info, dict):
            login_info = {}

        login_info.update(
            {
                "url": config.login_url,
                "username": config.username,
                "password": config.password,
            }
        )
        if config.storage_state is None:
            login_info.pop("storage_state", None)
        else:
            login_info["storage_state"] = deepcopy(config.storage_state)
        payload["login_info"] = login_info
        payload["resource_link_markers"] = list(config.resource_link_markers)
        payload["log_dir"] = config.log_dir

        self._atomic_write(payload)
        return config

    def save_storage_state(self, storage_state: Mapping[str, object]) -> SpiderBaseConfig:
        return self.save(self.load().with_storage_state(storage_state))

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


def _normalize_markers(candidates: list[object] | tuple[object, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for candidate in candidates:
        text = _text(candidate)
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()