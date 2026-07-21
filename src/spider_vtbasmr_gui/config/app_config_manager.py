from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from spider_vtbasmr_gui.config.app_config import AppConfig
from spider_vtbasmr_gui.project_paths import ProjectPaths


class AppConfigManager:
    def __init__(
        self,
        config_path: Path | None = None,
        *,
        project_paths: ProjectPaths | None = None,
    ) -> None:
        self._project_paths = project_paths or ProjectPaths.discover()
        self._config_path = config_path or self._project_paths.app_config_path

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> AppConfig:
        if not self._config_path.exists():
            return AppConfig.empty()
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"GUI 配置必须是 JSON object: {self._config_path}")
        return self._resolve_paths(AppConfig.from_dict(payload))

    def save(self, config: AppConfig) -> AppConfig:
        resolved_config = self._normalize(config)
        portable_config = replace(
            resolved_config,
            spider_base_config_path=self._portable_path(resolved_config.spider_base_config_path),
            spider_vtb_config_path=self._portable_path(resolved_config.spider_vtb_config_path),
            netdisk_config_path=self._portable_path(resolved_config.netdisk_config_path),
            seven_zip_path=self._portable_path(resolved_config.seven_zip_path),
        )
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(portable_config.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return resolved_config

    def _normalize(self, config: AppConfig) -> AppConfig:
        return replace(
            self._resolve_paths(config),
            transfer_root_dir=self._text(config.transfer_root_dir),
            nas_download_dir=self._text(config.nas_download_dir),
            decompression_password=self._text(config.decompression_password),
        )

    def _resolve_paths(self, config: AppConfig) -> AppConfig:
        return replace(
            config,
            spider_base_config_path=self._resolved_path(config.spider_base_config_path),
            spider_vtb_config_path=self._resolved_path(config.spider_vtb_config_path),
            netdisk_config_path=self._resolved_path(config.netdisk_config_path),
            seven_zip_path=self._resolved_path(config.seven_zip_path),
        )

    def _resolved_path(self, path_value: Path | None) -> Path | None:
        if path_value is None:
            return None
        return self._project_paths.resolve_project_path(path_value)

    def _portable_path(self, path_value: Path | None) -> Path | None:
        if path_value is None:
            return None
        return Path(self._project_paths.portable_project_path(path_value))

    @staticmethod
    def _text(value: str | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None