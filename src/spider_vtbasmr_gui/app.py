from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PySide6.QtWidgets import QApplication

from spider_vtbasmr.browser.playwright_browser_client import PlaywrightBrowserClient
from spider_vtbasmr_gui.config import AppConfigManager
from spider_vtbasmr_gui.controllers import ApplicationController
from spider_vtbasmr_gui.project_paths import ProjectPaths
from spider_vtbasmr_gui.services import RuntimeContextProvider
from spider_vtbasmr_gui.ui import MainWindow
from spider_vtbasmr_gui.ui.styles import build_application_stylesheet


@dataclass(slots=True)
class ApplicationRuntime:
    application: QApplication
    window: MainWindow
    controller: ApplicationController


def create_application_runtime(
    argv: Sequence[str] | None = None,
    *,
    project_paths: ProjectPaths | None = None,
) -> ApplicationRuntime:
    paths = project_paths or ProjectPaths.discover()
    os.chdir(paths.project_root)
    application = QApplication.instance() or QApplication(list(argv or []))
    application.setApplicationName("spider-vtbasmr-gui")
    application.setOrganizationName("vtb-asmr-tool")
    application.setStyle("Fusion")
    application.setStyleSheet(build_application_stylesheet())

    window = MainWindow()
    controller = ApplicationController(
        window,
        AppConfigManager(project_paths=paths),
        RuntimeContextProvider(paths),
    )
    controller.start()
    return ApplicationRuntime(application, window, controller)


def check_runtime_dependencies() -> int:
    client = PlaywrightBrowserClient()
    session = client.open_browser_session(is_headless=True)
    try:
        executable_path = Path(session.playwright.chromium.executable_path)
        if not executable_path.is_file():
            raise RuntimeError("Bundled Playwright Chromium is missing")
    finally:
        client.close_browser_session(session)
    return 0


def main() -> int:
    if "--check-runtime" in sys.argv[1:]:
        return check_runtime_dependencies()
    runtime = create_application_runtime(sys.argv)
    runtime.window.show()
    return runtime.application.exec()