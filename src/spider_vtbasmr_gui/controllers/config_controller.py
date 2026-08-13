from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from spider_vtbasmr_gui.config import AppConfig, AppConfigManager
from spider_vtbasmr_gui.services.runtime_context import RuntimeContextProvider
from spider_vtbasmr_gui.ui.pages.basic_config_page import BasicConfigPage


class ConfigController(QObject):
    config_applied = Signal(object)

    def __init__(
        self,
        page: BasicConfigPage,
        config_manager: AppConfigManager,
        context_provider: RuntimeContextProvider,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._page = page
        self._config_manager = config_manager
        self._context_provider = context_provider
        page.save_requested.connect(self.save)

    def load(self) -> AppConfig:
        try:
            config = self._config_manager.load()
        except Exception as error:
            self._page.show_status(f"读取配置失败：{error}", "error")
            return AppConfig.empty()
        self._page.set_config(config)
        return self._apply(config, "配置已加载并应用。")

    def save(self, config: AppConfig) -> None:
        try:
            saved_config = self._config_manager.save(config)
        except Exception as error:
            self._page.show_status(f"保存配置失败：{error}", "error")
            return
        self._page.set_config(saved_config)
        self._apply(saved_config, "配置已保存并立即应用。")

    def _apply(self, config: AppConfig, success_message: str) -> AppConfig:
        try:
            self._context_provider.configure(config)
        except Exception as error:
            self._page.show_status(f"配置已读取，但运行环境不可用：{error}", "warning")
            self.config_applied.emit(config)
            return config
        self._page.show_status(success_message, "success")
        self.config_applied.emit(config)
        return config