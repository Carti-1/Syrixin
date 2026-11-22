import sys
import time
from collections import deque

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QThread, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from logs.logger import LOG_FILE, log_error
from services.history import MetricsHistoryService
from ui.metrics_worker import MetricsWorker
from ui.widgets.cpu_chart import CpuChart
from utils.formatter import (
    format_battery,
    format_cpu,
    format_disk,
    format_ram,
    format_temperature,
)


class SyrixinWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._is_closing = False

        self.setWindowTitle("Syrixin")
        self.setMinimumSize(820, 640)
        self.resize(1120, 820)
        self._has_animated = False
        self.setStyleSheet("""
            QMainWindow, QWidget#central {
                background-color: #080a0f;
                color: #f2f5fa;
                font-family: "Segoe UI";
            }
            QLabel#subtitle { color: #8993a5; font-size: 13px; }
            QLabel#brandMark {
                background-color: #142b2b;
                border: 1px solid #24534d;
                border-radius: 17px;
                color: #65e0c6;
                font-size: 20px;
                font-weight: 800;
            }
            QLabel#status { color: #71d9b6; font-size: 12px; font-weight: 600; }
            QFrame#metricCard, QFrame#panel {
                background-color: #111620;
                border: 1px solid #202938;
                border-radius: 14px;
            }
            QTabWidget::pane {
                background: transparent;
                border: 0;
                top: 1px;
            }
            QTabBar::tab {
                background: transparent;
                color: #8993a5;
                padding: 11px 16px;
                margin-right: 5px;
                border-bottom: 2px solid transparent;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                color: #eafaf6;
                border-bottom: 2px solid #55d6be;
            }
            QTabBar::tab:hover { color: #f2f5fa; }
            QPushButton#refreshButton {
                background: #17211f;
                border: 1px solid #2b4842;
                border-radius: 8px;
                color: #a6e8d8;
                padding: 8px 13px;
            }
            QPushButton#refreshButton:hover { background: #1d302c; }
            QPlainTextEdit#logViewer {
                background: #0b0f16;
                border: 1px solid #202938;
                border-radius: 10px;
                color: #b9c5d4;
                padding: 12px;
                selection-background-color: #24534d;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)

        central_widget = QWidget()
        central_widget.setObjectName("central")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(26, 22, 26, 24)
        layout.setSpacing(18)
        layout.addWidget(self._create_header())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._create_overview(), "Visão geral")
        self.tabs.addTab(self._create_logs_page(), "Logs")
        self.tabs.addTab(self._create_ai_page(), "Assistente IA")
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(central_widget)

        self.history_service = MetricsHistoryService()
        self._chart_samples = deque(self.history_service.get_recent(limit=60), maxlen=60)
        # Save the first sample immediately; subsequent snapshots use 5s spacing.
        self._last_history_save = time.monotonic() - 5
        self.cpu_chart.update_data(self._chart_samples)

        self.log_refresh_timer = QTimer(self)
        self.log_refresh_timer.timeout.connect(self.refresh_logs)
        self.log_refresh_timer.start(2500)
        self.refresh_logs()

        self.metrics_thread = QThread(self)
        self.metrics_worker = MetricsWorker(interval_ms=1000)
        self.metrics_worker.moveToThread(self.metrics_thread)
        self.metrics_thread.started.connect(self.metrics_worker.start)
        self.metrics_worker.completed.connect(self.display_system_info)
        self.metrics_worker.failed.connect(self.log_collection_error)
        self.metrics_thread.finished.connect(self.metrics_worker.deleteLater)
        self.metrics_thread.start()

    def _create_header(self):
        header = QHBoxLayout()
        header.setSpacing(13)

        brand_mark = QLabel("S")
        brand_mark.setObjectName("brandMark")
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_mark.setFixedSize(46, 46)
        header.addWidget(brand_mark)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        title = QLabel("Syrixin")
        title.setStyleSheet("font-size: 25px; font-weight: 750; letter-spacing: 0.3px; color: #f5f7fb;")
        subtitle = QLabel("Visibilidade clara sobre a saúde do seu sistema")
        subtitle.setObjectName("subtitle")
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        header.addLayout(brand_text)
        header.addStretch(1)

        self.status_label = QLabel("●  Monitoramento ativo")
        self.status_label.setObjectName("status")
        header.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        wrapper = QWidget()
        wrapper.setLayout(header)
        return wrapper

    def _create_overview(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(16)

        self.cpu_card = MetricCard("◉", "CPU", "#55d6be")
        self.temperature_card = MetricCard("♨", "Temperatura da CPU", "#ff9f6e")
        self.memory_card = MetricCard("▤", "Memória", "#8f9cff")
        self.disk_card = MetricCard("◫", "Disco", "#54b7ff")
        self.battery_card = MetricCard("↯", "Bateria", "#c59aff")

        metrics_grid = QGridLayout()
        metrics_grid.setHorizontalSpacing(14)
        metrics_grid.setVerticalSpacing(14)
        for card, row, column in (
            (self.cpu_card, 0, 0),
            (self.temperature_card, 0, 1),
            (self.memory_card, 0, 2),
            (self.disk_card, 1, 0),
            (self.battery_card, 1, 1),
        ):
            metrics_grid.addWidget(card, row, column)
        for column in range(3):
            metrics_grid.setColumnStretch(column, 1)
        layout.addLayout(metrics_grid)

        chart_panel = QFrame()
        chart_panel.setObjectName("panel")
        chart_layout = QVBoxLayout(chart_panel)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        self.cpu_chart = CpuChart()
        chart_layout.addWidget(self.cpu_chart)
        layout.addWidget(chart_panel, 1)
        return page

    def _create_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel("Atividade recente")
        title.setStyleSheet("font-size: 16px; font-weight: 650; color: #edf2f8;")
        description = QLabel(
            "Alertas mostram a leitura do momento em que foram registrados; "
            "os cartões exibem a leitura atual."
        )
        description.setObjectName("subtitle")
        labels = QVBoxLayout()
        labels.setSpacing(3)
        labels.addWidget(title)
        labels.addWidget(description)
        toolbar.addLayout(labels)
        toolbar.addStretch(1)
        refresh_button = QPushButton("Atualizar")
        refresh_button.setObjectName("refreshButton")
        refresh_button.clicked.connect(lambda: self.refresh_logs())
        toolbar.addWidget(refresh_button)
        layout.addLayout(toolbar)

        self.log_viewer = QPlainTextEdit()
        self.log_viewer.setObjectName("logViewer")
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlaceholderText("Os eventos aparecerão aqui conforme o Syrixin os registrar.")
        self.log_viewer.setMaximumBlockCount(500)
        layout.addWidget(self.log_viewer, 1)
        return page

    def _create_ai_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.addStretch(1)

        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMaximumWidth(780)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(30, 28, 30, 30)
        panel_layout.setSpacing(14)

        eyebrow = QLabel("✦  PLANEJADO PARA UMA PRÓXIMA ETAPA")
        eyebrow.setStyleSheet("color: #55d6be; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        title = QLabel("Um assistente que entende o histórico do seu sistema")
        title.setWordWrap(True)
        title.setStyleSheet("color: #f3f6fb; font-size: 22px; font-weight: 700;")
        description = QLabel(
            "A IA deverá transformar medições em explicações úteis, usando o histórico "
            "local para apontar padrões e ajudar no diagnóstico."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #aab4c4; font-size: 14px; line-height: 1.4;")
        panel_layout.addWidget(eyebrow)
        panel_layout.addWidget(title)
        panel_layout.addWidget(description)

        ideas = QGridLayout()
        ideas.setHorizontalSpacing(12)
        ideas.setVerticalSpacing(12)
        for index, (name, detail) in enumerate((
            ("Encontrar padrões", "Ex.: picos de CPU que se repetem."),
            ("Explicar métricas", "Entender o que os números significam."),
            ("Sugerir otimizações", "Ações propostas para você revisar e autorizar."),
        )):
            idea = QFrame()
            idea.setStyleSheet("QFrame { background: #0c1119; border: 1px solid #202938; border-radius: 10px; }")
            idea_layout = QVBoxLayout(idea)
            idea_layout.setContentsMargins(14, 13, 14, 13)
            idea_layout.setSpacing(6)
            name_label = QLabel(name)
            name_label.setStyleSheet("color: #e7edf5; font-weight: 600;")
            detail_label = QLabel(detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet("color: #8993a5; font-size: 12px;")
            idea_layout.addWidget(name_label)
            idea_layout.addWidget(detail_label)
            ideas.addWidget(idea, index // 3, index % 3)
        panel_layout.addLayout(ideas)

        note = QLabel("A IA ainda não está conectada. Esta área apresenta o rumo planejado, sem executar ações no computador.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #788497; font-size: 12px;")
        panel_layout.addWidget(note)

        layout.addWidget(panel, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        return page

    def showEvent(self, event):
        super().showEvent(event)
        if self._has_animated:
            return
        self._has_animated = True
        effect = QGraphicsOpacityEffect(self.centralWidget())
        effect.setOpacity(0.0)
        self.centralWidget().setGraphicsEffect(effect)
        self._intro_animation = QPropertyAnimation(effect, b"opacity", self)
        self._intro_animation.setDuration(420)
        self._intro_animation.setStartValue(0.0)
        self._intro_animation.setEndValue(1.0)
        self._intro_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._intro_animation.start()

    def refresh_logs(self):
        try:
            lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
            content = "\n".join(lines[-500:]) or "Ainda não há eventos registrados."
        except FileNotFoundError:
            content = "Ainda não há eventos registrados."
        except OSError as error:
            content = f"Não foi possível ler o arquivo de logs: {error}"

        if content == self.log_viewer.toPlainText():
            return
        was_at_bottom = (
            self.log_viewer.verticalScrollBar().value()
            == self.log_viewer.verticalScrollBar().maximum()
        )
        self.log_viewer.setPlainText(content)
        if was_at_bottom:
            self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)

    def display_system_info(self, system):
        # A completed signal may already be queued when the window begins
        # closing. Ignore it before touching widgets or the SQLite connection.
        if self._is_closing:
            return

        self.status_label.setText("●  Monitoramento ativo")
        self.status_label.setStyleSheet("color: #71d9b6; font-size: 12px; font-weight: 600;")
        self.update_metrics(
            format_cpu(system.cpu),
            format_temperature(system.cpu_temp),
            format_ram(system.ram),
            format_disk(system.disk),
            format_battery(system.battery, system.battery_status),
        )
        self._chart_samples.appendleft((None, system.cpu))
        self.cpu_chart.update_data(self._chart_samples)

        # Refresh the chart every second, but keep durable history at 5-second
        # intervals so the database does not grow five times faster.
        now = time.monotonic()
        if now - self._last_history_save >= 5:
            try:
                self.history_service.save_snapshot(system)
                self._last_history_save = now
            except Exception as error:
                log_error(f"Failed to save desktop metrics history: {error}")
                self.refresh_logs()

    def update_metrics(self, cpu, temperature, memory, disk, battery):
        self.cpu_card.set_value(cpu)
        self.temperature_card.set_value(temperature)
        self.memory_card.set_value(memory)
        self.disk_card.set_value(disk)
        self.battery_card.set_value(battery)

    def log_collection_error(self, message):
        if self._is_closing:
            return
        log_error(f"Failed to collect desktop metrics: {message}")
        self.status_label.setText("●  Aguardando dados")
        self.status_label.setStyleSheet("color: #ffad7a; font-size: 12px; font-weight: 600;")
        self.refresh_logs()

    def closeEvent(self, event):
        self._is_closing = True
        self.log_refresh_timer.stop()
        self.metrics_worker.completed.disconnect(self.display_system_info)
        self.metrics_worker.failed.disconnect(self.log_collection_error)
        if self.metrics_thread.isRunning():
            self.metrics_thread.quit()
            self.metrics_thread.wait()
        self.history_service.close()
        event.accept()


class MetricCard(QFrame):
    def __init__(self, icon, title, accent, value="--"):
        super().__init__()
        self.setObjectName("metricCard")
        self.setMinimumHeight(112)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(17, 14, 17, 15)
        card_layout.setSpacing(8)

        heading = QGridLayout()
        heading.setHorizontalSpacing(9)
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: 700;")
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #aab4c4; font-size: 13px; font-weight: 600;")
        heading.addWidget(self.icon_label, 0, 0)
        heading.addWidget(self.title_label, 0, 1)
        heading.setColumnStretch(1, 1)
        card_layout.addLayout(heading)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #f3f6fb; font-size: 20px; font-weight: 600;")
        self.value_label.setWordWrap(True)
        card_layout.addWidget(self.value_label)
        card_layout.addStretch(1)

    def set_value(self, value):
        self.value_label.setText(str(value))


def main():
    app = QApplication(sys.argv)
    window = SyrixinWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
