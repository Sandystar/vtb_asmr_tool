from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

from spider_vtbasmr_gui.ui.task_runner import TaskRunner


class TaskCoordinator(QObject):
    busy_changed = Signal(bool, str)

    def __init__(self, task_runner: TaskRunner, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._task_runner = task_runner
        self._busy = False

    @property
    def is_busy(self) -> bool:
        return self._busy

    def run(
        self,
        task: Callable[[], object],
        *,
        busy_message: str,
        on_success: Callable[[object], None],
        on_error: Callable[[str], None],
    ) -> bool:
        if self._busy:
            return False
        self._busy = True
        self.busy_changed.emit(True, busy_message)

        def handle_error(message: str, traceback_text: str) -> None:
            print(traceback_text, flush=True)
            on_error(message)

        def handle_finished() -> None:
            self._busy = False
            self.busy_changed.emit(False, "等待下一步操作。")

        self._task_runner.run(
            task,
            on_success=on_success,
            on_error=handle_error,
            on_finished=handle_finished,
        )
        return True