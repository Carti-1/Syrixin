import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFrame,
    QGridLayout
)

from utils.formatter import (
    format_battery,
    format_cpu,
    format_disk,
    format_ram,
)

from PySide6.QtCore import QThread
from ui.metrics_worker import MetricsWorker


class SyrixinWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Syrixin")
        self.resize(900, 600)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        title = QLabel("Syrixin")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.status_label = QLabel("Coletando métricas...")

        self.cpu_card = MetricCard("CPU")
        self.memory_card = MetricCard("Memória")
        self.disk_card = MetricCard("Disco")
        self.battery_card = MetricCard("Bateria")

        metrics_grid = QGridLayout()
        metrics_grid.addWidget(self.cpu_card, 0, 0)
        metrics_grid.addWidget(self.memory_card, 0, 1)
        metrics_grid.addWidget(self.disk_card, 1, 0)
        metrics_grid.addWidget(self.battery_card, 1, 1)

        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addLayout(metrics_grid)

        self.setCentralWidget(central_widget)

        self.metrics_thread = QThread(self)
        self.metrics_worker = MetricsWorker()
        self.metrics_worker.moveToThread(self.metrics_thread)

        self.metrics_thread.started.connect(self.metrics_worker.run)
        self.metrics_worker.completed.connect(self.display_system_info)
        self.metrics_worker.failed.connect(self.show_collection_error)
        self.metrics_worker.finished.connect(self.metrics_thread.quit)
        self.metrics_worker.finished.connect(self.metrics_worker.deleteLater)

        self.metrics_thread.start()

    def update_metrics(self, cpu, memory, disk, battery):
        self.cpu_card.set_value(cpu)
        self.memory_card.set_value(memory)
        self.disk_card.set_value(disk)
        self.battery_card.set_value(battery)

    def display_system_info(self, system):
        self.update_metrics(
            format_cpu(system.cpu),
            format_ram(system.ram),
            format_disk(system.disk),
            format_battery(system.battery, system.battery_status),
        )
        self.status_label.setText("Métricas atualizadas")

    def show_collection_error(self, message):
        self.status_label.setText(f"Falha ao coletar métricas: {message}")

    def closeEvent(self, event):
        if self.metrics_thread.isRunning():
            self.metrics_thread.quit()
            self.metrics_thread.wait()
        event.accept()

class MetricCard(QFrame):
    def __init__(self, titulo, valor="--"):
        super().__init__()

        self.setFrameShape(QFrame.Shape.StyledPanel)

        card_layout = QVBoxLayout(self)

        self.title_label = QLabel(titulo)
        self.value_label = QLabel(valor)

        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))




def main():
    
    app = QApplication(sys.argv)
    window = SyrixinWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()