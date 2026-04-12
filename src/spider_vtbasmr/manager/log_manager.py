from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.scraper.detail_page_scraper import DownloadLinkItem


@dataclass(slots=True)
class LogRecord:
    tag_name: str
    published_at: str
    saved_detail_file_path: str
    download_links: list[DownloadLinkItem]

    def to_dict(self) -> dict[str, object]:
        return {
            "tag_name": self.tag_name,
            "published_at": self.published_at,
            "saved_detail_file_path": self.saved_detail_file_path,
            "download_links": [download_link.to_dict() for download_link in self.download_links],
        }


class LogManager:
    def __init__(
        self,
        *,
        log_file_name: str | None = None,
        log_dir_path: str | Path | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigManager()
        resolved_log_dir_path = Path(log_dir_path) if log_dir_path is not None else self._config_manager.get_log_dir_path()
        self.log_dir_path = resolved_log_dir_path
        self.log_file_name = self._resolve_log_file_name(log_file_name)
        self.log_file_path = self.log_dir_path / self.log_file_name

    def append(self, log_record: LogRecord) -> Path:
        self.log_dir_path.mkdir(parents=True, exist_ok=True)
        output_data = self._load_existing_records()
        output_data.append(log_record.to_dict())
        self.log_file_path.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.log_file_path

    def _load_existing_records(self) -> list[dict[str, object]]:
        if not self.log_file_path.exists():
            return []

        try:
            loaded_data = json.loads(self.log_file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(loaded_data, list):
            return []
        return [item for item in loaded_data if isinstance(item, dict)]

    @staticmethod
    def _resolve_log_file_name(log_file_name: str | None) -> str:
        if log_file_name:
            normalized_log_file_name = Path(log_file_name).name.strip()
            if normalized_log_file_name.endswith(".json"):
                return normalized_log_file_name
            return f"{normalized_log_file_name}.json"

        return f"{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.json"
