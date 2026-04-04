from pathlib import Path


class ArchiveManager:
    def __init__(self, archive_file_path: str | Path) -> None:
        self.archive_file_path = Path(archive_file_path)
        self.archive_item_ids: list[str] = []
        self.load_archive()

    def load_archive(self) -> None:
        self.archive_item_ids = []
        if not self.archive_file_path.exists():
            return

        with self.archive_file_path.open("r", encoding="utf-8") as archive_file:
            for line in archive_file:
                archive_item_id = line.strip()
                if archive_item_id:
                    self.archive_item_ids.append(archive_item_id)

    def save_archive(self) -> None:
        self.archive_file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.archive_file_path.open("w", encoding="utf-8") as archive_file:
            for archive_item_id in self.archive_item_ids:
                archive_file.write(archive_item_id + "\n")
        self.load_archive()

    def is_in_archive(self, archive_item_id: str) -> bool:
        return archive_item_id in self.archive_item_ids

    def add_to_archive(self, archive_item_id: str) -> None:
        if self.is_in_archive(archive_item_id):
            return
        self.archive_item_ids.append(archive_item_id)
        self.save_archive()

    def remove_from_archive(self, archive_item_id: str) -> None:
        if not self.is_in_archive(archive_item_id):
            return
        self.archive_item_ids.remove(archive_item_id)
        self.save_archive()
