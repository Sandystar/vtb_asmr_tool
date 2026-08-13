from __future__ import annotations

from dataclasses import dataclass

from spider_vtbasmr.manager.base_config import SpiderBaseConfig
from spider_vtbasmr_gui.config.fnos_config import FnosConfig
from spider_vtbasmr_gui.config.seven_zip_config import SevenZipConfig
from spider_vtbasmr_gui.config.vtb_list_config import VtbListConfig


@dataclass(frozen=True, slots=True)
class AppConfig:
    spider_base_config: SpiderBaseConfig | None = None
    vtb_list_config: VtbListConfig | None = None
    fnos_config: FnosConfig | None = None
    seven_zip_config: SevenZipConfig | None = None

    @classmethod
    def empty(cls) -> "AppConfig":
        return cls()

    def has_transfer_settings(self) -> bool:
        return self.fnos_config is not None and self.fnos_config.has_transfer_settings()

    def has_decompression_settings(self) -> bool:
        return self.seven_zip_config is not None and self.seven_zip_config.has_executable()