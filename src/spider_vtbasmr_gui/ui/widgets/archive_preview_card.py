from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from spider_vtbasmr_gui.services.decompression_service import DiscoveredArchiveFile


class ArchivePreviewCard(QWidget):
    def __init__(self, item: DiscoveredArchiveFile, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("itemCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        title = QLabel(f"{item.tag_name} · {item.published_date}")
        title.setObjectName("itemTitle")
        source = QLabel(str(item.source_file_path))
        source.setObjectName("helperText")
        target = QLabel(f"输出到 {item.final_output_dir}")
        target.setObjectName("linkText")
        layout.addWidget(title)
        layout.addWidget(source)
        layout.addWidget(target)