from __future__ import annotations

from pathlib import Path

from spider_vtbasmr.manager.base_config import BaseConfigStore, SpiderBaseConfig


DEFAULT_CONFIG_PATH = Path("config/vtbasmr_base.json")


class ConfigManager:
    def __init__(
        self,
        config_path: Path | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        self._project_root = (project_root or Path.cwd()).expanduser().resolve(strict=False)
        self._config_path = self._resolve_path(config_path or DEFAULT_CONFIG_PATH)
        self._base_config_store = BaseConfigStore(
            self._config_path,
            project_root=self._project_root,
        )
        self._base_config = self._base_config_store.load()

    @property
    def config_path(self) -> Path:
        return self._config_path

    def get_login_url(self) -> str:
        return self._require_login_value(self._base_config.login_url, "url")

    def get_login_username(self) -> str:
        return self._require_login_value(self._base_config.username, "username")

    def get_login_password(self) -> str:
        return self._require_login_value(self._base_config.password, "password")

    def get_site_origin(self) -> str:
        return self._base_config.site_origin

    def get_storage_state(self) -> dict[str, object] | None:
        if self._base_config.storage_state is None:
            return None
        return dict(self._base_config.storage_state)

    def save_storage_state(self, storage_state: dict[str, object]) -> None:
        self._base_config_store.save_storage_state(storage_state)
        self._reload()

    def get_log_dir_path(self) -> Path:
        if not self._base_config.log_dir:
            raise ValueError(f"Missing log_dir in config file: {self._config_path}")
        return self._resolve_path(Path(self._base_config.log_dir))

    def get_resource_link_markers(self) -> tuple[str, ...]:
        return self._base_config.resource_link_markers

    def _resolve_path(self, path_value: Path) -> Path:
        expanded_path = path_value.expanduser()
        if expanded_path.is_absolute():
            return expanded_path.resolve(strict=False)
        return (self._project_root / expanded_path).resolve(strict=False)

    def _reload(self) -> None:
        self._base_config = self._base_config_store.load()

    @staticmethod
    def _require_login_value(value: str, field_name: str) -> str:
        if not value:
            raise ValueError(f"Missing login_info.{field_name}")
        return value