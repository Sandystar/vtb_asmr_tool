import json
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_VTB_CONFIG_PATH = Path("config/vtb_list.json")


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
    def __init__(
        self,
        config_path: Path | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        self._project_root = (project_root or Path.cwd()).expanduser().resolve(strict=False)
        self._config_path = self._resolve_path(config_path or DEFAULT_VTB_CONFIG_PATH)
        self._config_data = self._load_config_data()

    @property
    def config_path(self) -> Path:
        return self._config_path

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

    def _resolve_path(self, path_value: Path) -> Path:
        expanded_path = path_value.expanduser()
        if expanded_path.is_absolute():
            return expanded_path.resolve(strict=False)
        return (self._project_root / expanded_path).resolve(strict=False)

    def _load_config_data(self) -> dict[str, object]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"VTB config file not found: {self._config_path}")

        with self._config_path.open("r", encoding="utf-8-sig") as config_file:
            config_data = json.load(config_file)
        if not isinstance(config_data, dict):
            raise ValueError(f"VTB config file must contain a JSON object: {self._config_path}")
        return config_data

    def _build_vtb_config(self, raw_vtb_config: dict[str, object]) -> VtbConfig:
        name = self._get_required_field(raw_vtb_config, "name")
        url = self._get_required_field(raw_vtb_config, "url")
        archive_file_path = self._resolve_path(Path(self._get_required_field(raw_vtb_config, "archive_file_path")))
        save_dir_path = self._resolve_path(Path(self._get_required_field(raw_vtb_config, "save_dir_path")))

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
