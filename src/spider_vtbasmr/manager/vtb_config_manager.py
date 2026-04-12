import json
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock


DEFAULT_VTB_CONFIG_PATH = Path(".config/vtb.json")


@dataclass(slots=True)
class VtbConfig:
    name: str
    url: str
    archive_file_path: Path
    save_dir_path: Path

    def to_dict(self) -> dict[str, object]:
        config_dict = asdict(self)
        config_dict["archive_file_path"] = str(self.archive_file_path)
        config_dict["save_dir_path"] = str(self.save_dir_path)
        return config_dict


class VtbConfigManager:
    _instance: "VtbConfigManager | None" = None
    _lock: Lock = Lock()

    def __new__(cls, config_path: Path | None = None) -> "VtbConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._is_initialized = False
        return cls._instance

    def __init__(self, config_path: Path | None = None) -> None:
        if self._is_initialized:
            return

        self._config_path = config_path or DEFAULT_VTB_CONFIG_PATH
        self._config_data = self._load_config_data()
        self._is_initialized = True

    def get_vtb_config(self, tag_name: str) -> VtbConfig:
        raw_vtb_config = self._config_data.get(tag_name)
        if not isinstance(raw_vtb_config, dict):
            raise KeyError(f"VTB config not found for tag: {tag_name}")
        return self._build_vtb_config(raw_vtb_config)

    def get_all_vtb_configs(self) -> list[VtbConfig]:
        return [
            self._build_vtb_config(raw_vtb_config)
            for raw_vtb_config in self._config_data.values()
            if isinstance(raw_vtb_config, dict)
        ]

    def get_all_vtb_names(self) -> list[str]:
        return [vtb_config.name for vtb_config in self.get_all_vtb_configs()]

    def _load_config_data(self) -> dict[str, object]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"VTB config file not found: {self._config_path}")

        with self._config_path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    def _build_vtb_config(self, raw_vtb_config: dict[str, object]) -> VtbConfig:
        name = self._get_required_field(raw_vtb_config, "name")
        url = self._get_required_field(raw_vtb_config, "url")
        archive_file_path = Path(self._get_required_field(raw_vtb_config, "archive_file_path"))
        save_dir_path = Path(self._get_required_field(raw_vtb_config, "save_dir_path"))

        return VtbConfig(
            name=name,
            url=url,
            archive_file_path=archive_file_path,
            save_dir_path=save_dir_path,
        )

    def _get_required_field(self, raw_vtb_config: dict[str, object], field_name: str) -> str:
        field_value = raw_vtb_config.get(field_name)
        if not field_value:
            raise ValueError(f"Missing {field_name} in VTB config file: {self._config_path}")
        return str(field_value)
