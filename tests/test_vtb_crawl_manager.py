from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.manager.vtb_crawl_manager import CrawlMode, VtbCrawlManager


TARGET_TAG_NAME = "利香"


def main() -> None:
    vtb_crawl_manager = VtbCrawlManager()
    crawl_summary = vtb_crawl_manager.crawl_vtb(
        tag_name=TARGET_TAG_NAME,
        crawl_mode=CrawlMode.UNTIL_ARCHIVED,
        is_headless=True,
    )
    print(json.dumps(crawl_summary.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
