from PySide6.QtCore import QObject, QTimer, Signal, Slot

from services.monitoring import collect_system_info


class MetricsWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, interval_ms=1000):
        super().__init__()
        self.interval_ms = interval_ms
        self.timer = None

    @Slot()
    def start(self):
        self.timer = QTimer(self)
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self.collect)

        self.collect()
        self.timer.start()

    @Slot()
    def collect(self):
        try:
            system = collect_system_info()
            self.completed.emit(system)
        except Exception as error:
            self.failed.emit(str(error))
