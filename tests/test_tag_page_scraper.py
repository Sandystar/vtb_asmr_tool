from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import json

from spider_vtbasmr.scraper.tag_page_scraper import TagPageScraper


TARGET_TAG_URL = "https://vtbasmr.xyz/tag/%e5%88%a9%e9%a6%99"


def main() -> None:
    tag_page_scraper = TagPageScraper()
    tag_page_result = tag_page_scraper.scrape_tag_page(
        page_url=TARGET_TAG_URL,
        is_headless=True,
    )
    print(json.dumps(tag_page_result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
