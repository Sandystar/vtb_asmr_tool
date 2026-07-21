from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager
from spider_vtbasmr_gui.config.app_config import AppConfig
from spider_vtbasmr_gui.integrations.netdisk.credential import FnosCredentialStore
from spider_vtbasmr_gui.project_paths import ProjectPaths


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    app_config: AppConfig
    project_paths: ProjectPaths
    spider_config: ConfigManager
    vtb_config: VtbConfigManager
    credential_store: FnosCredentialStore


class RuntimeContextProvider:
    def __init__(self, project_paths: ProjectPaths) -> None:
        self._project_paths = project_paths
        self._context: RuntimeContext | None = None
        self._error: str | None = None

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def is_ready(self) -> bool:
        return self._context is not None

    def configure(self, config: AppConfig) -> RuntimeContext:
        self._context = None
        self._error = None
        try:
            base_path = self._required_file(config.spider_base_config_path, "抓取基础配置")
            vtb_path = self._required_file(config.spider_vtb_config_path, "VTB 配置")
            netdisk_path = self._required_file(config.netdisk_config_path, "FNOS 配置")
            context = RuntimeContext(
                app_config=config,
                project_paths=self._project_paths,
                spider_config=ConfigManager(base_path, project_root=self._project_paths.project_root),
                vtb_config=VtbConfigManager(vtb_path, project_root=self._project_paths.project_root),
                credential_store=FnosCredentialStore(netdisk_path),
            )
        except Exception as error:
            self._error = str(error)
            raise
        self._context = context
        return context

    def require(self) -> RuntimeContext:
        if self._context is None:
            detail = f" {self._error}" if self._error else ""
            raise RuntimeError(f"运行配置尚未就绪。{detail}".strip())
        return self._context

    @staticmethod
    def _required_file(path_value: Path | None, label: str) -> Path:
        if path_value is None:
            raise ValueError(f"缺少{label}路径")
        path = path_value.expanduser().resolve(strict=False)
        if not path.is_file():
            raise FileNotFoundError(f"{label}文件不存在: {path}")
        return path