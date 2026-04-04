import json
from dataclasses import dataclass
from pathlib import Path

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
    def __init__(self, log_file_path: str | Path) -> None:
        self.log_file_path = Path(log_file_path)

    def save(self, log_records: list[LogRecord]) -> Path:
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_data = [log_record.to_dict() for log_record in log_records]
        self.log_file_path.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.log_file_path
