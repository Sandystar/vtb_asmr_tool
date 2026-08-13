from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from spider_vtbasmr_gui.config.vtb_list_config import VtbListItem


class VtbListItemEditor(QWidget):
    remove_requested = Signal(object)

    def __init__(self, item: VtbListItem | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("itemCard")
        self._original = item or VtbListItem("", "", "", "")
        self._build()
        self.set_item(self._original)

    def set_item(self, item: VtbListItem) -> None:
        self._original = item
        self.name_edit.setText(item.name)
        self.url_edit.setText(item.url)
        self.archive_file_edit.setText(item.archive_file_path)
        self.save_dir_edit.setText(item.save_dir_path)

    def current_item(self) -> VtbListItem:
        name = self.name_edit.text().strip()
        return replace(
            self._original,
            name=name,
            url=self.url_edit.text().strip(),
            archive_file_path=self.archive_file_edit.text().strip(),
            save_dir_path=self.save_dir_edit.text().strip(),
            tag_name=name,
        )

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        remove_button = QPushButton("删除")
        remove_button.setObjectName("vtbTableDeleteButton")
        remove_button.clicked.connect(lambda: self.remove_requested.emit(self))

        self.name_edit = self._add_field(
            layout,
            "名字",
            "VTB 名字",
            trailing_widget=remove_button,
            first_row=True,
        )
        self.url_edit = self._add_field(layout, "链接", "https://...")
        self.archive_file_edit = self._add_field(
            layout,
            "归档记录文件",
            ".data/archive/name.txt",
        )
        self.save_dir_edit = self._add_field(
            layout,
            "保存文件夹",
            ".data/save/name",
            last_row=True,
        )

    @staticmethod
    def _add_field(
        layout: QVBoxLayout,
        label_text: str,
        placeholder: str,
        *,
        trailing_widget: QWidget | None = None,
        first_row: bool = False,
        last_row: bool = False,
    ) -> QLineEdit:
        row = QWidget()
        row.setObjectName("vtbTableRow")
        row.setProperty("firstRow", first_row)
        row.setProperty("lastRow", last_row)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        label = QLabel(label_text)
        label.setObjectName("vtbTableLabel")
        label.setFixedWidth(108)
        line_edit = QLineEdit()
        line_edit.setObjectName("vtbTableInput")
        line_edit.setPlaceholderText(placeholder)
        row_layout.addWidget(label)
        row_layout.addWidget(line_edit, 1)
        if trailing_widget is not None:
            operation_cell = QWidget()
            operation_cell.setObjectName("vtbTableActionCell")
            operation_layout = QHBoxLayout(operation_cell)
            operation_layout.setContentsMargins(6, 4, 6, 4)
            operation_layout.addWidget(trailing_widget)
            row_layout.addWidget(operation_cell)
        layout.addWidget(row)
        return line_edit