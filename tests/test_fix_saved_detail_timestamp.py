from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager


DEFAULT_SAVE_TIMESTAMP = 0


def main() -> None:
    vtb_config_manager = VtbConfigManager()
    fix_summaries: list[dict[str, object]] = []

    for vtb_config in vtb_config_manager.get_all_vtb_configs():
        fix_summary = fix_saved_detail_timestamp(
            save_dir_path=vtb_config.save_dir_path,
            default_save_timestamp=DEFAULT_SAVE_TIMESTAMP,
        )
        fix_summary["tag_name"] = vtb_config.name
        fix_summaries.append(fix_summary)

    print(json.dumps(fix_summaries, ensure_ascii=False, indent=2))


def fix_saved_detail_timestamp(*, save_dir_path: Path, default_save_timestamp: int) -> dict[str, object]:
    json_file_paths = sorted(save_dir_path.rglob("*.json"))
    checked_file_count = 0
    fixed_file_count = 0

    for json_file_path in json_file_paths:
        checked_file_count += 1

        try:
            json_data = json.loads(json_file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not isinstance(json_data, dict):
            continue
        if "save_timestamp" in json_data:
            continue

        json_data["save_timestamp"] = default_save_timestamp
        json_file_path.write_text(
            json.dumps(json_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        fixed_file_count += 1

    return {
        "save_dir_path": str(save_dir_path),
        "checked_file_count": checked_file_count,
        "fixed_file_count": fixed_file_count,
        "default_save_timestamp": default_save_timestamp,
    }


if __name__ == "__main__":
    main()
