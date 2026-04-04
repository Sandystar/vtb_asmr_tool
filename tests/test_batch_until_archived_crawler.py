from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.main.batch_until_archived_crawler import BatchUntilArchivedCrawler


def main() -> None:
    batch_until_archived_crawler = BatchUntilArchivedCrawler()
    batch_crawl_result = batch_until_archived_crawler.crawl_all_vtb_configs(
        is_headless=True,
    )
    print(json.dumps(batch_crawl_result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
