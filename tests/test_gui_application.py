from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from spider_vtbasmr_gui import app as app_module
from spider_vtbasmr_gui.app import create_application_runtime
from spider_vtbasmr_gui.controllers.resource_transfer_controller import ResourceTransferController
from spider_vtbasmr_gui.project_paths import ProjectPaths
from spider_vtbasmr_gui.ui.task_runner import TaskRunner
from spider_vtbasmr_gui.ui.widgets import SectionCard


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def build_test_project(root: Path) -> ProjectPaths:
    paths = ProjectPaths.from_root(root)
    write_json(
        paths.spider_base_config_path,
        {
            "login_info": {
                "url": "https://example.test/login",
                "username": "user",
                "password": "password",
                "storage_state": {"cookies": [], "origins": []},
            },
            "resource_link_markers": ["https://pan.example/s"],
            "log_dir": ".data/logs",
        },
    )
    write_json(paths.vtb_list_config_path, {})
    write_json(
        paths.fnos_config_path,
        {
            "base_url": "http://fnos.test",
            "trans_share_dir": "/transfer",
            "download_dir": "/nas",
        },
    )
    write_json(
        paths.seven_zip_config_path,
        {"7z_path": None, "decompress_password": None},
    )
    return paths


def test_application_constructs_all_pages_without_starting_side_effects(tmp_path: Path) -> None:
    original_cwd = Path.cwd()
    runtime = create_application_runtime([], project_paths=build_test_project(tmp_path))
    try:
        assert runtime.window.current_page_index == 0
        for index in range(4):
            runtime.window.switch_page(index)
            assert runtime.window.current_page_index == index
        assert runtime.window.crawl_page.selected_tag_names() == []
    finally:
        runtime.window.close()
        os.chdir(original_cwd)


def test_crawl_page_uses_vertical_sections_and_updates_progress(tmp_path: Path) -> None:
    original_cwd = Path.cwd()
    runtime = create_application_runtime([], project_paths=build_test_project(tmp_path))
    try:
        page = runtime.window.crawl_page
        page_layout = page.layout()
        assert isinstance(page_layout, QVBoxLayout)

        cards = [
            page_layout.itemAt(index).widget()
            for index in range(page_layout.count())
            if isinstance(page_layout.itemAt(index).widget(), SectionCard)
        ]
        assert [
            card.findChild(QLabel, "sectionTitle").text()
            for card in cards
        ] == ["抓取进度", "更新状态", "任务设置"]

        login_button = next(
            button
            for button in page.findChildren(QPushButton)
            if button.text() == "登录并保存状态"
        )
        assert login_button.text() == "登录并保存状态"

        task_card = cards[2]
        task_columns = task_card.findChild(QWidget, "contentPanel")
        assert task_columns is not None
        assert isinstance(task_columns.layout(), QHBoxLayout)
        assert task_columns.findChild(QWidget, "taskParameters") is not None
        assert task_columns.findChild(QWidget, "vtbSelection") is not None

        page.show_crawl_progress("测试 VTB", 2, 7)
        progress_bar = page.findChild(QProgressBar, "crawlProgressBar")
        progress_values = {
            label.text()
            for label in page.findChildren(QLabel, "progressMetricValue")
        }
        assert progress_values == {"测试 VTB", "2", "7"}
        assert progress_bar.maximum() == 7
        assert progress_bar.value() == 2
        assert progress_bar.format() == "2 / 7"
    finally:
        runtime.window.close()
        os.chdir(original_cwd)


def test_resource_login_prompt_requires_manual_agreement() -> None:
    class SignalStub:
        def __init__(self) -> None:
            self.callbacks = []

        def connect(self, callback) -> None:
            self.callbacks.append(callback)

    class PageStub:
        def __init__(self) -> None:
            self.login_requested = SignalStub()
            self.parse_requested = SignalStub()
            self.transfer_requested = SignalStub()
            self.statuses: list[tuple[str, str]] = []

        def show_login_status(self, message: str, tone: str) -> None:
            self.statuses.append((message, tone))

    class TaskStub:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def run(self, task, **kwargs) -> bool:
            self.calls.append({"task": task, **kwargs})
            return True

    page = PageStub()
    tasks = TaskStub()
    service = SimpleNamespace(capture_fnos_auth=lambda: "done")
    controller = ResourceTransferController(page, service, tasks)  # type: ignore[arg-type]

    controller.login()

    message, tone = page.statuses[-1]
    assert "手动勾选用户协议和隐私协议" in message
    assert "授权登录" in message
    assert tone == "warning"
    assert len(tasks.calls) == 1


def test_main_shows_window_and_returns_qt_event_loop_exit_code(monkeypatch) -> None:
    received_argv: list[list[str]] = []
    shown: list[bool] = []
    application = SimpleNamespace(exec=lambda: 17)
    window = SimpleNamespace(show=lambda: shown.append(True))

    def create_runtime(argv):
        received_argv.append(argv)
        return SimpleNamespace(application=application, window=window)

    monkeypatch.setattr(app_module.sys, "argv", ["spider-vtbasmr-gui"])
    monkeypatch.setattr(app_module, "create_application_runtime", create_runtime)

    assert app_module.main() == 17
    assert received_argv == [["spider-vtbasmr-gui"]]
    assert shown == [True]


def test_task_runner_delivers_background_result_to_qt_loop(tmp_path: Path) -> None:
    original_cwd = Path.cwd()
    runtime = create_application_runtime([], project_paths=build_test_project(tmp_path))
    results: list[object] = []
    errors: list[str] = []
    loop = QEventLoop()
    runner = TaskRunner()
    try:
        runner.run(
            lambda: 42,
            on_success=results.append,
            on_error=lambda message, _: errors.append(message),
            on_finished=loop.quit,
        )
        QTimer.singleShot(3000, loop.quit)
        loop.exec()
        assert results == [42]
        assert errors == []
    finally:
        runtime.window.close()
        os.chdir(original_cwd)