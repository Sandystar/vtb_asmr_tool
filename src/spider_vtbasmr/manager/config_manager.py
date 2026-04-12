import json
from pathlib import Path
from threading import Lock


DEFAULT_CONFIG_PATH = Path(".config/config.json")


class ConfigManager:
    _instance: "ConfigManager | None" = None
    _lock: Lock = Lock()

    def __new__(cls, config_path: Path | None = None) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._is_initialized = False
        return cls._instance

    def __init__(self, config_path: Path | None = None) -> None:
        if self._is_initialized:
            return

        self._config_path = config_path or DEFAULT_CONFIG_PATH
        self._config_data = self._load_config_data()
        self._is_initialized = True

    def get_browser_channel(self) -> str | None:
        return self._config_data.get("browser", {}).get("channel")

    def get_login_url(self) -> str:
        return self._get_required_login_value("url")

    def get_login_username(self) -> str:
        return self._get_required_login_value("username")

    def get_login_password(self) -> str:
        return self._get_required_login_value("password")

    def get_login_success_prefix(self) -> str:
        return self._get_required_login_value("success_prefix")

    def get_login_state_file_path(self) -> Path:
        return Path(self._get_required_login_value("state_file_path"))

    def get_log_dir_path(self) -> Path:
        log_dir = self._config_data.get("log_dir")
        if not log_dir:
            raise ValueError(f"Missing log_dir in config file: {self._config_path}")
        return Path(str(log_dir))

    def get_download_link_info(self) -> dict[str, str]:
        download_link_info = self._config_data.get("download_link_info", {})
        if not isinstance(download_link_info, dict):
            raise ValueError(f"download_link_info must be an object in config file: {self._config_path}")
        return {
            str(link_type): str(link_prefix)
            for link_type, link_prefix in download_link_info.items()
            if link_prefix
        }

    def _load_config_data(self) -> dict[str, object]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        with self._config_path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    def _get_required_login_value(self, field_name: str) -> str:
        login_info = self._config_data.get("login_info", {})
        field_value = login_info.get(field_name)
        if not field_value:
            raise ValueError(f"Missing login_info.{field_name} in config file: {self._config_path}")
        return str(field_value)
