from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class AppConfig:
    spider_base_config_path: Path | None = None
    spider_vtb_config_path: Path | None = None
    netdisk_config_path: Path | None = None
    transfer_root_dir: str | None = None
    nas_download_dir: str | None = None
    seven_zip_path: Path | None = None
    decompression_password: str | None = None

    @classmethod
    def empty(cls) -> "AppConfig":
        return cls()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "AppConfig":
        return cls(
            spider_base_config_path=cls._path(payload.get("spider_base_config_path")),
            spider_vtb_config_path=cls._path(payload.get("spider_vtb_config_path")),
            netdisk_config_path=cls._path(payload.get("baidu_netdisk_config_path")),
            transfer_root_dir=cls._text(payload.get("trans_share_dir")),
            nas_download_dir=cls._text(payload.get("download_dir")),
            seven_zip_path=cls._path(payload.get("7z_path")),
            decompression_password=cls._text(payload.get("decompress_password")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "spider_base_config_path": self._path_text(self.spider_base_config_path),
            "spider_vtb_config_path": self._path_text(self.spider_vtb_config_path),
            "baidu_netdisk_config_path": self._path_text(self.netdisk_config_path),
            "trans_share_dir": self.transfer_root_dir,
            "download_dir": self.nas_download_dir,
            "7z_path": self._path_text(self.seven_zip_path),
            "decompress_password": self.decompression_password,
        }

    def missing_runtime_fields(self) -> list[str]:
        fields: list[str] = []
        if self.spider_base_config_path is None:
            fields.append("抓取基础配置")
        if self.spider_vtb_config_path is None:
            fields.append("VTB 配置")
        if self.netdisk_config_path is None:
            fields.append("FNOS 配置")
        return fields

    def has_transfer_settings(self) -> bool:
        return bool(self.transfer_root_dir and self.nas_download_dir)

    def has_decompression_settings(self) -> bool:
        return self.seven_zip_path is not None

    @staticmethod
    def _path(value: object) -> Path | None:
        text = AppConfig._text(value)
        return Path(text) if text else None

    @staticmethod
    def _path_text(value: Path | None) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None