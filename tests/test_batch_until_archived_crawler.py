from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.core import CrawlMode, PageOrder, VtbCrawler


TARGET_LOG_FILE_NAME = "批量抓取-测试日志"


def main() -> None:
    vtb_crawler = VtbCrawler()
    batch_crawl_result = vtb_crawler.crawl_vtb_list(
        crawl_mode=CrawlMode.UNTIL_ARCHIVED,
        page_order=PageOrder.ASCENDING,
        log_file_name=TARGET_LOG_FILE_NAME,
        is_headless=True,
    )
    print(json.dumps(batch_crawl_result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
