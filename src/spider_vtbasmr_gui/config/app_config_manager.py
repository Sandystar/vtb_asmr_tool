from __future__ import annotations

from dataclasses import replace

from spider_vtbasmr.manager.base_config import BaseConfigStore, SpiderBaseConfig
from spider_vtbasmr_gui.config.app_config import AppConfig
from spider_vtbasmr_gui.config.fnos_config import FnosConfigStore
from spider_vtbasmr_gui.config.seven_zip_config import SevenZipConfigStore
from spider_vtbasmr_gui.config.vtb_list_config import VtbListConfigStore
from spider_vtbasmr_gui.project_paths import ProjectPaths


class AppConfigManager:
    def __init__(self, *, project_paths: ProjectPaths | None = None) -> None:
        self._project_paths = project_paths or ProjectPaths.discover()

    def load(self) -> AppConfig:
        paths = self._project_paths
        return AppConfig(
            spider_base_config=BaseConfigStore(
                paths.spider_base_config_path,
                project_root=paths.project_root,
            ).load(),
            vtb_list_config=VtbListConfigStore(
                paths.vtb_list_config_path,
                project_root=paths.project_root,
            ).load(),
            fnos_config=FnosConfigStore(paths.fnos_config_path).load(),
            seven_zip_config=SevenZipConfigStore(
                paths.seven_zip_config_path,
                project_root=paths.project_root,
            ).load(),
        )

    def save(self, config: AppConfig) -> AppConfig:
        paths = self._project_paths
        updated = config

        if config.spider_base_config is not None:
            updated = replace(
                updated,
                spider_base_config=self._save_spider_base_config(config.spider_base_config),
            )

        if config.vtb_list_config is not None:
            updated = replace(
                updated,
                vtb_list_config=VtbListConfigStore(
                    paths.vtb_list_config_path,
                    project_root=paths.project_root,
                ).save(config.vtb_list_config),
            )

        if config.fnos_config is not None:
            submitted = config.fnos_config
            updated = replace(
                updated,
                fnos_config=FnosConfigStore(paths.fnos_config_path).update_visible_fields(
                    base_url=submitted.credential.base_url,
                    username=submitted.credential.username,
                    password=submitted.credential.password,
                    transfer_root_dir=submitted.transfer_root_dir,
                    nas_download_dir=submitted.nas_download_dir,
                ),
            )

        if config.seven_zip_config is not None:
            submitted = config.seven_zip_config
            updated = replace(
                updated,
                seven_zip_config=SevenZipConfigStore(
                    paths.seven_zip_config_path,
                    project_root=paths.project_root,
                ).update_visible_fields(
                    executable_path=submitted.executable_path,
                    default_password=submitted.default_password,
                ),
            )

        return updated

    def save_spider_base_config(self, config: AppConfig) -> AppConfig:
        if config.spider_base_config is None:
            return config
        return replace(
            config,
            spider_base_config=self._save_spider_base_config(config.spider_base_config),
        )

    def _save_spider_base_config(self, submitted: SpiderBaseConfig) -> SpiderBaseConfig:
        paths = self._project_paths
        store = BaseConfigStore(
            paths.spider_base_config_path,
            project_root=paths.project_root,
        )
        current = store.load() if paths.spider_base_config_path.is_file() else None
        persisted = replace(
            submitted,
            login_url=submitted.login_url.strip(),
            username=submitted.username.strip(),
            password=submitted.password.strip(),
            resource_link_markers=tuple(
                dict.fromkeys(
                    marker.strip()
                    for marker in submitted.resource_link_markers
                    if marker.strip()
                )
            ),
            log_dir=submitted.log_dir.strip(),
            storage_state=(
                current.storage_state
                if current is not None and current.storage_state is not None
                else submitted.storage_state
            ),
        )
        return store.save(persisted)