import json
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(".config/config.json")


class ConfigManager:
    def __init__(
        self,
        config_path: Path | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        self._project_root = (project_root or Path.cwd()).expanduser().resolve(strict=False)
        self._config_path = self._resolve_path(config_path or DEFAULT_CONFIG_PATH)
        self._config_data = self._load_config_data()

    @property
    def config_path(self) -> Path:
        return self._config_path

    def get_browser_channel(self) -> str | None:
        channel = self._browser_settings().get("channel")
        return str(channel).strip() if channel else None

    def get_browser_profile_directory(self) -> str:
        profile_directory = self._browser_settings().get("profile_directory")
        return str(profile_directory).strip() if profile_directory else "Default"

    def use_existing_browser_profile(self) -> bool:
        value = self._browser_settings().get("use_existing_profile", True)
        if isinstance(value, str):
            return value.strip().lower() not in {"0", "false", "no", "off"}
        return bool(value)

    def get_browser_user_data_dir(self) -> Path | None:
        settings = self._browser_settings()
        configured_path = settings.get("user_data_dir")
        if configured_path:
            return self._resolve_path(Path(str(configured_path)))

        channel = (self.get_browser_channel() or "").lower()
        default_directories = {
            "edge": Path.home() / "AppData/Local/Microsoft/Edge/User Data",
            "msedge": Path.home() / "AppData/Local/Microsoft/Edge/User Data",
            "chrome": Path.home() / "AppData/Local/Google/Chrome/User Data",
        }
        user_data_dir = default_directories.get(channel)
        return user_data_dir if user_data_dir and user_data_dir.exists() else None

    def get_login_url(self) -> str:
        return self._get_required_login_value("url")

    def get_login_username(self) -> str:
        return self._get_required_login_value("username")

    def get_login_password(self) -> str:
        return self._get_required_login_value("password")

    def get_login_success_prefix(self) -> str:
        return self._get_required_login_value("success_prefix")

    def get_login_state_file_path(self) -> Path:
        return self._resolve_path(Path(self._get_required_login_value("state_file_path")))

    def get_log_dir_path(self) -> Path:
        log_dir = self._config_data.get("log_dir")
        if not log_dir:
            raise ValueError(f"Missing log_dir in config file: {self._config_path}")
        return self._resolve_path(Path(str(log_dir)))

    def get_download_link_info(self) -> dict[str, str]:
        download_link_info = self._config_data.get("download_link_info", {})
        if not isinstance(download_link_info, dict):
            raise ValueError(f"download_link_info must be an object in config file: {self._config_path}")
        return {
            str(link_type): str(link_prefix)
            for link_type, link_prefix in download_link_info.items()
            if link_prefix
        }

    def _browser_settings(self) -> dict[str, object]:
        settings = self._config_data.get("browser", {})
        if not isinstance(settings, dict):
            raise ValueError(f"browser must be an object in config file: {self._config_path}")
        return settings

    def _resolve_path(self, path_value: Path) -> Path:
        expanded_path = path_value.expanduser()
        if expanded_path.is_absolute():
            return expanded_path.resolve(strict=False)
        return (self._project_root / expanded_path).resolve(strict=False)

    def _load_config_data(self) -> dict[str, object]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        with self._config_path.open("r", encoding="utf-8-sig") as config_file:
            config_data = json.load(config_file)
        if not isinstance(config_data, dict):
            raise ValueError(f"Config file must contain a JSON object: {self._config_path}")
        return config_data

    def _get_required_login_value(self, field_name: str) -> str:
        login_info = self._config_data.get("login_info", {})
        if not isinstance(login_info, dict):
            raise ValueError(f"login_info must be an object in config file: {self._config_path}")
        field_value = login_info.get(field_name)
        if not field_value:
            raise ValueError(f"Missing login_info.{field_name} in config file: {self._config_path}")
        return str(field_value)
