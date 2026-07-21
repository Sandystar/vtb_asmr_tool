from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from spider_vtbasmr_gui.services.resource_transfer_service import TransferResourceItem


class ResourceItemCard(QWidget):
    def __init__(self, item: TransferResourceItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("itemCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        title = QLabel(f"{item.tag_name} · {item.published_at}")
        title.setObjectName("itemTitle")
        detail = QLabel(item.detail_file_stem)
        detail.setObjectName("helperText")
        link = QLabel(item.link_url)
        link.setObjectName("linkText")
        link.setTextInteractionFlags(link.textInteractionFlags() | link.textInteractionFlags().TextSelectableByMouse)
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addWidget(link)