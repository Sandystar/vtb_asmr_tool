from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from spider_vtbasmr.manager.base_config import SpiderBaseConfig
from spider_vtbasmr_gui.config import AppConfig
from spider_vtbasmr_gui.config.fnos_config import FnosConfig, FnosCredential
from spider_vtbasmr_gui.config.seven_zip_config import SevenZipConfig
from spider_vtbasmr_gui.config.vtb_list_config import VtbListConfig, VtbListItem
from spider_vtbasmr_gui.ui.pages.basic_config_page import BasicConfigPage


def test_data_config_page_is_vertical_and_hides_internal_state() -> None:
    application = QApplication.instance() or QApplication([])
    page = BasicConfigPage()
    page.set_config(
        AppConfig(
            spider_base_config=SpiderBaseConfig(
                login_url="https://example.test/login",
                username="user",
                password="secret",
                resource_link_markers=("https://pan.baidu.com/s",),
                log_dir=".data/logs",
                storage_state={"cookies": []},
            ),
        )
    )

    assert page._login_url.text() == "https://example.test/login"
    assert page._password_login.echoMode() == page._password_login.EchoMode.Password
    assert page._markers.count() == 1
    assert page._markers.item(0).text() == "https://pan.baidu.com/s"
    assert page._markers.height() < 80
    assert page._markers.editTriggers() == page._markers.EditTrigger.NoEditTriggers
    assert not any(
        button.text() in {"新增链接标记", "删除选中"}
        for button in page.findChildren(QPushButton)
    )
    assert page._log_dir.objectName() == ""
    assert page.findChild(type(page._markers), "markerList") is page._markers
    page.close()
    application.processEvents()


def test_fnos_folders_survive_page_round_trip_and_belong_to_fnos_card() -> None:
    application = QApplication.instance() or QApplication([])
    page = BasicConfigPage()
    page.set_config(
        AppConfig(
            fnos_config=FnosConfig(
                transfer_root_dir="/00-vtbasmr.net",
                nas_download_dir="/vol2/1000/UserData/Download/BaiduNetdisk/asmrdh.net",
            )
        )
    )

    assert page._transfer_root.text() == "/00-vtbasmr.net"
    assert page._nas_dir.text() == "/vol2/1000/UserData/Download/BaiduNetdisk/asmrdh.net"
    assert page._transfer_root.parentWidget().parentWidget() is page._fnos_url.parentWidget().parentWidget()
    assert page._transfer_root.parentWidget().parentWidget() is not page._seven_zip.parentWidget().parentWidget()
    current = page.current_config()
    assert current.fnos_config is not None
    assert current.fnos_config.transfer_root_dir == "/00-vtbasmr.net"
    assert current.fnos_config.nas_download_dir == "/vol2/1000/UserData/Download/BaiduNetdisk/asmrdh.net"
    page.close()
    application.processEvents()


def test_decompression_config_survives_page_round_trip_and_uses_named_card() -> None:
    application = QApplication.instance() or QApplication([])
    page = BasicConfigPage()
    page.set_config(
        AppConfig(
            seven_zip_config=SevenZipConfig(
                executable_path=Path("thirdtool/7-Zip/7z.exe"),
                default_password="asmrdh.net",
            )
        )
    )

    assert page._seven_zip.text() == "thirdtool/7-Zip/7z.exe"
    assert not any(button.text() == "浏览" for button in page.findChildren(QPushButton))
    assert page._password.text() == "asmrdh.net"
    assert page._password.echoMode() == page._password.EchoMode.Password
    titles = [label.text() for label in page.findChildren(QLabel) if label.objectName() == "sectionTitle"]
    assert "解压配置" in titles
    assert "资源处理配置" not in titles
    current = page.current_config()
    assert current.seven_zip_config == SevenZipConfig(
        executable_path=Path("thirdtool/7-Zip/7z.exe"),
        default_password="asmrdh.net",
    )
    page.close()
    application.processEvents()


def test_vtb_list_section_supports_edit_add_and_delete() -> None:
    application = QApplication.instance() or QApplication([])
    page = BasicConfigPage()
    page.set_config(
        AppConfig(
            vtb_list_config=VtbListConfig(
                (
                    VtbListItem(
                        name="旧名字",
                        url="https://example.test/old",
                        archive_file_path=".data/archive/old.txt",
                        save_dir_path=".data/save/old",
                        extra_fields={"future_setting": True},
                    ),
                    VtbListItem(
                        name="待删除",
                        url="https://example.test/delete",
                        archive_file_path=".data/archive/delete.txt",
                        save_dir_path=".data/save/delete",
                    ),
                )
            )
        )
    )

    titles = [label.text() for label in page.findChildren(QLabel) if label.objectName() == "sectionTitle"]
    assert "抓取列表配置" in titles
    assert len(page._vtb_item_editors) == 2
    first = page._vtb_item_editors[0]
    assert not any(label.text() == "抓取目标" for label in first.findChildren(QLabel))
    assert [
        label.text()
        for label in first.findChildren(QLabel)
        if label.objectName() == "vtbTableLabel"
    ] == ["名字", "链接", "归档记录文件", "保存文件夹"]
    assert not any(button.text() == "浏览" for button in first.findChildren(QPushButton))
    rows = [widget for widget in first.findChildren(QWidget) if widget.objectName() == "vtbTableRow"]
    assert len(rows) == 4
    assert rows[0].property("firstRow") is True
    assert rows[-1].property("lastRow") is True
    for line_edit in (
        first.name_edit,
        first.url_edit,
        first.archive_file_edit,
        first.save_dir_edit,
    ):
        assert line_edit.objectName() == "vtbTableInput"
        assert line_edit.parentWidget().objectName() == "vtbTableRow"
    first.name_edit.setText("新名字")
    first.url_edit.setText("https://example.test/new")
    first.archive_file_edit.setText(".data/archive/new.txt")
    first.save_dir_edit.setText(".data/save/new")
    page._remove_vtb_item(page._vtb_item_editors[1])
    added = page._add_vtb_item()
    added.name_edit.setText("新增名字")
    added.url_edit.setText("https://example.test/added")
    added.archive_file_edit.setText(".data/archive/added.txt")
    added.save_dir_edit.setText(".data/save/added")

    current = page.current_config()
    assert current.vtb_list_config is not None
    assert [item.name for item in current.vtb_list_config.items] == ["新名字", "新增名字"]
    assert current.vtb_list_config.items[0].url == "https://example.test/new"
    assert current.vtb_list_config.items[0].archive_file_path == ".data/archive/new.txt"
    assert current.vtb_list_config.items[0].save_dir_path == ".data/save/new"
    assert current.vtb_list_config.items[0].extra_fields == {"future_setting": True}
    page.close()
    application.processEvents()


def test_fnos_fields_are_masked_and_hidden_runtime_fields_survive_round_trip() -> None:
    application = QApplication.instance() or QApplication([])
    page = BasicConfigPage()
    page.set_config(
        AppConfig(
            fnos_config=FnosConfig(
                credential=FnosCredential(
                    base_url="http://fnos.test",
                    username="user",
                    password="secret",
                    cookie="language=zh-CN; fnos-token=opaque",
                    verify_ssl=False,
                    appid="app-id",
                    product="netdisk",
                    device_id="device-id",
                ),
                transfer_root_dir="/transfer",
                nas_download_dir="/nas",
            )
        )
    )

    assert page._fnos_password.echoMode() == page._fnos_password.EchoMode.Password
    assert page._fnos_url.text() == "http://fnos.test"
    assert page._fnos_username.text() == "user"
    current = page.current_config()
    assert current.fnos_config is not None
    assert current.fnos_config.credential.cookie == "language=zh-CN; fnos-token=opaque"
    assert current.fnos_config.credential.device_id == "device-id"
    assert current.fnos_config.credential.verify_ssl is False
    assert current.fnos_config.transfer_root_dir == "/transfer"
    page.close()
    application.processEvents()
