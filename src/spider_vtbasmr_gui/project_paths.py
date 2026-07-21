from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    project_root: Path
    data_dir: Path
    app_config_path: Path

    @classmethod
    def discover(cls, start_path: Path | None = None) -> "ProjectPaths":
        start = (start_path or Path(__file__)).resolve(strict=False)
        candidates = [start] if start.is_dir() else list(start.parents)
        for candidate in candidates:
            if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
                return cls.from_root(candidate)
        return cls.from_root(Path.cwd())

    @classmethod
    def from_root(cls, project_root: Path) -> "ProjectPaths":
        resolved_root = project_root.expanduser().resolve(strict=False)
        data_dir = resolved_root / ".data"
        return cls(
            project_root=resolved_root,
            data_dir=data_dir,
            app_config_path=data_dir / "config" / "config.json",
        )

    def resolve_project_path(self, path_value: str | Path) -> Path:
        path = Path(path_value).expanduser()
        if path.is_absolute():
            return path.resolve(strict=False)
        return (self.project_root / path).resolve(strict=False)

    def portable_project_path(self, path_value: Path) -> str:
        resolved_path = self.resolve_project_path(path_value)
        try:
            return resolved_path.relative_to(self.project_root).as_posix()
        except ValueError:
            return str(resolved_path)