from PySide6.QtCore import QObject, Signal, Slot

from services.monitoring import collect_system_info


class MetricsWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self):
        try:
            system = collect_system_info()
            self.completed.emit(system)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()