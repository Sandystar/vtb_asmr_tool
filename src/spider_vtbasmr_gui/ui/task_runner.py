from __future__ import annotations

import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class TaskSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(str, str)
    finished = Signal()


class CallableTask(QRunnable):
    def __init__(self, task: Callable[[], object]) -> None:
        super().__init__()
        self._task = task
        self.signals = TaskSignals()

    def run(self) -> None:
        try:
            result = self._task()
        except Exception as error:
            self.signals.failed.emit(str(error), traceback.format_exc())
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class TaskRunner(QObject):
    def __init__(self, parent: QObject | None = None, thread_pool: QThreadPool | None = None) -> None:
        super().__init__(parent)
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._active_tasks: set[CallableTask] = set()

    def run(
        self,
        task: Callable[[], object],
        *,
        on_success: Callable[[object], None],
        on_error: Callable[[str, str], None],
        on_finished: Callable[[], None],
    ) -> None:
        runnable = CallableTask(task)
        self._active_tasks.add(runnable)
        runnable.signals.succeeded.connect(on_success)
        runnable.signals.failed.connect(on_error)
        runnable.signals.finished.connect(on_finished)
        runnable.signals.finished.connect(lambda: self._active_tasks.discard(runnable))
        self._thread_pool.start(runnable)