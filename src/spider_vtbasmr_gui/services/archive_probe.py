from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol


class ArchiveProbe(Protocol):
    def detect_format(self, path: Path) -> str | None: ...


class SevenZipArchiveProbe:
    def __init__(
        self,
        seven_zip_path: Path,
        *,
        password: str | None = None,
        timeout_seconds: float = 30,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._seven_zip_path = seven_zip_path
        self._password = password
        self._timeout_seconds = timeout_seconds
        self._runner = runner

    def detect_format(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        command = self._command(path)
        try:
            result = self._runner(
                command,
                check=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"7z 检测压缩格式超时: {path}") from error
        except OSError as error:
            raise RuntimeError(f"无法运行 7z 检测压缩格式: {self._seven_zip_path}") from error

        return self._parse_format(result.stdout, result.stderr)

    def _command(self, path: Path) -> list[str]:
        command = [
            str(self._seven_zip_path),
            "l",
            "-slt",
            "-bd",
            "-y",
            str(path),
        ]
        if self._password:
            command.append(f"-p{self._password}")
        return command

    @staticmethod
    def _parse_format(*outputs: str) -> str | None:
        for line in SevenZipArchiveProbe._lines(outputs):
            key, separator, value = line.partition("=")
            if separator and key.strip().lower() == "type" and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _lines(outputs: Sequence[str]) -> list[str]:
        return [line.strip() for output in outputs for line in output.splitlines()]