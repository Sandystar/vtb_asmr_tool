from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager
from spider_vtbasmr.scraper.detail_page_scraper import DetailPageScraper


TARGET_TAG_NAME = "利香"


def main() -> None:
    detail_page_scraper = DetailPageScraper()
    vtb_config_manager = VtbConfigManager()
    vtb_config = vtb_config_manager.get_vtb_config(TARGET_TAG_NAME)
    target_save_dir_path = vtb_config.save_dir_path
    target_log_file_path = vtb_config.log_file_path
    json_file_paths = sorted(target_save_dir_path.rglob("*.json"))
    fixed_saved_file_count = 0
    fixed_log_record_count = 0

    for json_file_path in json_file_paths:
        json_data = json.loads(json_file_path.read_text(encoding="utf-8"))
        detail_page_result = json_data.get("detail_page_result", {})
        download_links = detail_page_result.get("download_links", [])
        hidden_content_text = str(detail_page_result.get("hidden_content_text", ""))

        if download_links:
            continue

        fixed_download_links = [
            download_link.to_dict()
            for download_link in detail_page_scraper.extract_download_links_from_text(hidden_content_text)
        ]
        if not fixed_download_links:
            continue

        detail_page_result["download_links"] = fixed_download_links
        json_data["detail_page_result"] = detail_page_result
        json_file_path.write_text(
            json.dumps(json_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        fixed_saved_file_count += 1
        print(f"fixed saved file {json_file_path}")

    if target_log_file_path.exists():
        log_records = json.loads(target_log_file_path.read_text(encoding="utf-8"))
        for log_record in log_records:
            log_download_links = log_record.get("download_links", [])
            if log_download_links:
                continue

            saved_detail_file_path = Path(str(log_record.get("saved_detail_file_path", "")))
            if not saved_detail_file_path.exists():
                continue

            saved_json_data = json.loads(saved_detail_file_path.read_text(encoding="utf-8"))
            detail_page_result = saved_json_data.get("detail_page_result", {})
            detail_download_links = detail_page_result.get("download_links", [])
            if not detail_download_links:
                hidden_content_text = str(detail_page_result.get("hidden_content_text", ""))
                detail_download_links = [
                    download_link.to_dict()
                    for download_link in detail_page_scraper.extract_download_links_from_text(hidden_content_text)
                ]
                if detail_download_links:
                    detail_page_result["download_links"] = detail_download_links
                    saved_json_data["detail_page_result"] = detail_page_result
                    saved_detail_file_path.write_text(
                        json.dumps(saved_json_data, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )

            if not detail_download_links:
                continue

            log_record["download_links"] = detail_download_links
            fixed_log_record_count += 1
            print(f"fixed log record {saved_detail_file_path}")

        target_log_file_path.write_text(
            json.dumps(log_records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "tag_name": TARGET_TAG_NAME,
                "target_save_dir_path": str(target_save_dir_path),
                "target_log_file_path": str(target_log_file_path),
                "fixed_saved_file_count": fixed_saved_file_count,
                "fixed_log_record_count": fixed_log_record_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
