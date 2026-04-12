import json
import re
from pathlib import Path
from time import time

from spider_vtbasmr.scraper.detail_page_scraper import DetailPageResult
from spider_vtbasmr.scraper.tag_page_scraper import CoverItem


class SaveManager:
    def __init__(self, save_dir_path: str | Path) -> None:
        self.save_dir_path = Path(save_dir_path)

    def save_cover_detail_result(self, cover_item: CoverItem, detail_page_result: DetailPageResult) -> Path:
        resolved_published_at = self.resolve_published_at(
            detail_published_at=detail_page_result.published_at,
            cover_published_at=cover_item.published_at,
        )
        target_file_path = self._build_target_file_path(
            post_id=cover_item.post_id,
            published_at=resolved_published_at,
        )
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "post_id": cover_item.post_id,
            "save_timestamp": int(time()),
            "cover_item": cover_item.to_dict(),
            "detail_page_result": detail_page_result.to_dict(),
        }
        target_file_path.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target_file_path

    def resolve_published_at(self, *, detail_published_at: str, cover_published_at: str) -> str:
        for published_at_candidate in [detail_published_at, cover_published_at]:
            normalized_published_at = self._normalize_published_at(published_at_candidate)
            if normalized_published_at:
                return normalized_published_at
        raise ValueError(
            "Invalid published_at format. "
            f"detail_published_at={detail_published_at!r}, cover_published_at={cover_published_at!r}"
        )

    def _build_target_file_path(self, post_id: str, published_at: str) -> Path:
        year_text, month_text = self._extract_year_month(published_at)
        return self.save_dir_path / year_text / month_text / f"{post_id}.json"

    def _extract_year_month(self, published_at: str) -> tuple[str, str]:
        normalized_published_at = self._normalize_published_at(published_at)
        if not normalized_published_at:
            raise ValueError(f"Invalid published_at format: {published_at}")
        date_text = normalized_published_at.split(" ", 1)[0]
        date_parts = date_text.split("-")
        year_text = date_parts[0]
        month_text = date_parts[1]
        return year_text, month_text

    def _normalize_published_at(self, published_at: str) -> str:
        normalized_text = published_at.strip()
        if not normalized_text:
            return ""
        normalized_text = normalized_text.replace("年", "-").replace("月", "-").replace("日", "")
        date_match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", normalized_text)
        if date_match is None:
            return ""
        year_text, month_text, day_text = date_match.groups()
        return f"{year_text}-{int(month_text):02d}-{int(day_text):02d}"
