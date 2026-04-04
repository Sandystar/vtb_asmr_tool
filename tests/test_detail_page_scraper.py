from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import json

from spider_vtbasmr.scraper.detail_page_scraper import DetailPageScraper


TARGET_DETAIL_URL = "https://vtbasmr.xyz/202603245699.html"


def main() -> None:
    detail_page_scraper = DetailPageScraper()
    detail_page_result = detail_page_scraper.scrape_detail_page(
        page_url=TARGET_DETAIL_URL,
        is_headless=True,
    )
    print(json.dumps(detail_page_result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
