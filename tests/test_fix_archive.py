from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.manager.vtb_config_manager import VtbConfigManager


def main() -> None:
    vtb_config_manager = VtbConfigManager()
    archive_fix_summaries: list[dict[str, object]] = []

    for vtb_config in vtb_config_manager.get_all_vtb_configs():
        archive_fix_summary = fix_archive_file(
            archive_file_path=vtb_config.archive_file_path,
            save_dir_path=vtb_config.save_dir_path,
        )
        archive_fix_summary["tag_name"] = vtb_config.name
        archive_fix_summaries.append(archive_fix_summary)

    print(json.dumps(archive_fix_summaries, ensure_ascii=False, indent=2))


def fix_archive_file(*, archive_file_path: Path, save_dir_path: Path) -> dict[str, object]:
    saved_short_id_by_archive_id = build_saved_short_id_by_archive_id(save_dir_path=save_dir_path)
    original_archive_item_ids = load_archive_item_ids(archive_file_path)
    fixed_archive_item_ids: list[str] = []
    replaced_item_count = 0
    removed_duplicate_count = 0

    for archive_item_id in original_archive_item_ids:
        normalized_archive_item_id = archive_item_id.strip()
        if not normalized_archive_item_id:
            continue

        fixed_archive_item_id = resolve_short_archive_item_id(
            archive_item_id=normalized_archive_item_id,
            saved_short_id_by_archive_id=saved_short_id_by_archive_id,
        )
        if fixed_archive_item_id != normalized_archive_item_id:
            replaced_item_count += 1

        if any(
            archive_item_ids_match(existing_archive_item_id, fixed_archive_item_id)
            for existing_archive_item_id in fixed_archive_item_ids
        ):
            removed_duplicate_count += 1
            continue

        fixed_archive_item_ids.append(fixed_archive_item_id)

    if fixed_archive_item_ids != original_archive_item_ids:
        archive_file_path.parent.mkdir(parents=True, exist_ok=True)
        archive_file_path.write_text(
            "".join(f"{archive_item_id}\n" for archive_item_id in fixed_archive_item_ids),
            encoding="utf-8",
        )

    return {
        "archive_file_path": str(archive_file_path),
        "save_dir_path": str(save_dir_path),
        "original_count": len(original_archive_item_ids),
        "fixed_count": len(fixed_archive_item_ids),
        "replaced_item_count": replaced_item_count,
        "removed_duplicate_count": removed_duplicate_count,
        "changed": fixed_archive_item_ids != original_archive_item_ids,
    }


def build_saved_short_id_by_archive_id(*, save_dir_path: Path) -> dict[str, str]:
    saved_short_id_by_archive_id: dict[str, str] = {}

    for saved_json_file_path in save_dir_path.rglob("*.json"):
        try:
            saved_json_data = json.loads(saved_json_file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not isinstance(saved_json_data, dict):
            continue

        cover_item = saved_json_data.get("cover_item", {})
        if not isinstance(cover_item, dict):
            continue

        archive_item_id = extract_archive_item_id_from_detail_url(
            str(cover_item.get("detail_url", "")).strip(),
        )
        if not archive_item_id:
            continue

        short_post_id = str(cover_item.get("post_id", "")).strip()
        if not short_post_id:
            continue

        saved_short_id_by_archive_id[archive_item_id] = short_post_id
        saved_short_id_by_archive_id[short_post_id] = short_post_id

    return saved_short_id_by_archive_id


def extract_archive_item_id_from_detail_url(detail_url: str) -> str:
    detail_path = urlparse(detail_url).path.rstrip("/")
    return Path(detail_path).stem


def resolve_short_archive_item_id(*, archive_item_id: str, saved_short_id_by_archive_id: dict[str, str]) -> str:
    matched_short_archive_item_id = saved_short_id_by_archive_id.get(archive_item_id)
    if matched_short_archive_item_id:
        return matched_short_archive_item_id

    derived_short_archive_item_id = extract_short_archive_item_id(archive_item_id)
    if derived_short_archive_item_id:
        return derived_short_archive_item_id

    return archive_item_id


def extract_short_archive_item_id(archive_item_id: str) -> str:
    normalized_archive_item_id = archive_item_id.strip()
    if not normalized_archive_item_id.isdigit():
        return ""
    if len(normalized_archive_item_id) <= 8:
        return normalized_archive_item_id

    date_prefix = normalized_archive_item_id[:8]
    short_archive_item_id = normalized_archive_item_id[8:]
    if not short_archive_item_id:
        return normalized_archive_item_id
    if len(date_prefix) == 8 and date_prefix.isdigit():
        return short_archive_item_id
    return normalized_archive_item_id


def load_archive_item_ids(archive_file_path: Path) -> list[str]:
    if not archive_file_path.exists():
        return []
    return [
        line.strip()
        for line in archive_file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def archive_item_ids_match(left_archive_item_id: str, right_archive_item_id: str) -> bool:
    normalized_left_archive_item_id = left_archive_item_id.strip()
    normalized_right_archive_item_id = right_archive_item_id.strip()

    if not normalized_left_archive_item_id or not normalized_right_archive_item_id:
        return False
    if normalized_left_archive_item_id == normalized_right_archive_item_id:
        return True
    if not normalized_left_archive_item_id.isdigit() or not normalized_right_archive_item_id.isdigit():
        return False

    if len(normalized_left_archive_item_id) > len(normalized_right_archive_item_id):
        return normalized_left_archive_item_id.endswith(normalized_right_archive_item_id)
    if len(normalized_right_archive_item_id) > len(normalized_left_archive_item_id):
        return normalized_right_archive_item_id.endswith(normalized_left_archive_item_id)
    return False


if __name__ == "__main__":
    main()
