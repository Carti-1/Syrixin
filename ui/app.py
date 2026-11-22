import sys
import time
from collections import deque

from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from logs.logger import LOG_FILE, clear_log_file, log_error
from services.hardware import HardwareMonitorUnavailable, get_hardware_inventory
from services.history import MetricsHistoryService
from ui.metrics_worker import MetricsWorker
from ui.widgets.cpu_chart import CpuSparkline
from ui.widgets.metric_indicator import MetricLevelIndicator
from ui.widgets.temperature_indicator import TemperatureIndicator
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
        self.setStyleSheet("""
            QMainWindow, QWidget#central {
                background-color: #080a0f;
                color: #f2f5fa;
                font-family: "Segoe UI";
            }
            QLabel#subtitle { color: #8993a5; font-size: 13px; }
            QLabel#status { color: #71d9b6; font-size: 12px; font-weight: 600; }
            QFrame#metricCard, QFrame#panel {
                background-color: #111620;
                border: 1px solid #202938;
                border-radius: 14px;
            }
            QWidget#sectionNavigation {
                background: #111620;
                border: 1px solid #202938;
                border-radius: 12px;
            }
            QPushButton#navButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 9px;
                color: #8993a5;
                padding: 12px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#navButton:hover {
                background: #19212d;
                color: #f2f5fa;
            }
            QPushButton#navButton:checked {
                background: #172a29;
                border: 1px solid #285148;
                color: #b8f2e4;
            }
            QPushButton#refreshButton {
                background: #17211f;
                border: 1px solid #2b4842;
                border-radius: 8px;
                color: #a6e8d8;
                padding: 8px 13px;
            }
            QPushButton#refreshButton:hover { background: #1d302c; }
            QPushButton#clearLogsButton {
                background: #241719;
                border: 1px solid #59343a;
                border-radius: 8px;
                color: #ffb3b8;
                padding: 8px 13px;
            }
            QPushButton#clearLogsButton:hover { background: #382024; }
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
            QTreeWidget#hardwareTree {
                background: #0b0f16;
                border: 1px solid #202938;
                border-radius: 10px;
                color: #d6deea;
                padding: 8px;
            }
            QTreeWidget#hardwareTree::item { padding: 7px 4px; }
            QTreeWidget#hardwareTree::item:selected { background: #17312d; }
            QTreeWidget#hardwareTree QHeaderView::section {
                background: #111620;
                border: 0;
                color: #8993a5;
                padding: 8px;
            }
            QLineEdit#hardwareSearch {
                background: #0b0f16;
                border: 1px solid #202938;
                border-radius: 8px;
                color: #e3eaf3;
                padding: 10px 12px;
                selection-background-color: #24534d;
            }
            QLabel#hardwareEmptyState {
                background: #0d1119;
                border: 1px dashed #293444;
                border-radius: 12px;
                color: #aab4c4;
                font-size: 14px;
                padding: 28px;
            }
        """)

        central_widget = QWidget()
        central_widget.setObjectName("central")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(26, 22, 26, 24)
        layout.setSpacing(18)
        layout.addWidget(self._create_header())

        self.sections = QStackedWidget()
        self.sections.addWidget(self._create_overview())
        self.hardware_tab_index = self.sections.addWidget(self._create_hardware_page())
        self.sections.addWidget(self._create_logs_page())
        self.sections.addWidget(self._create_ai_page())
        navigation = QWidget()
        navigation.setObjectName("sectionNavigation")
        navigation_layout = QHBoxLayout(navigation)
        navigation_layout.setContentsMargins(7, 7, 7, 7)
        navigation_layout.setSpacing(7)
        self.section_buttons = []
        section_labels = (
            "⌂  Visão geral",
            "▦  Hardware",
            "☷  Logs",
            "✧  Assistente IA",
        )
        for index, label in enumerate(section_labels):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, section_index=index: self._navigate_to_section(section_index)
            )
            navigation_layout.addWidget(button, 1)
            self.section_buttons.append(button)
        self.section_buttons[0].setChecked(True)

        layout.addWidget(navigation)
        layout.addWidget(self.sections, 1)
        self.setCentralWidget(central_widget)

        self.history_service = MetricsHistoryService()
        self._chart_samples = deque(self.history_service.get_recent(limit=60), maxlen=60)
        # Save the first sample immediately; subsequent snapshots use 5s spacing.
        self._last_history_save = time.monotonic() - 5
        self.cpu_card.set_visual_data(self._chart_samples)

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
        header.setSpacing(12)
        title = QLabel("Syrixin")
        title.setStyleSheet("font-size: 29px; font-weight: 750; letter-spacing: 0.3px; color: #f5f7fb;")
        header.addWidget(title)
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

        self.cpu_card = MetricCard("◉", "CPU", "#55d6be", visual="cpu")
        self.memory_card = MetricCard("▤", "Memória", "#8f9cff", visual="memory")
        self.disk_card = MetricCard("◫", "Disco", "#54b7ff", visual="disk")
        self.temperature_card = TemperatureCard()
        self.battery_card = MetricCard("↯", "Bateria", "#c59aff", visual="battery")

        metrics_rows = QVBoxLayout()
        metrics_rows.setSpacing(14)
        first_row = QHBoxLayout()
        first_row.setSpacing(14)
        for card in (self.cpu_card, self.memory_card, self.disk_card):
            first_row.addWidget(card, 1)
        second_row = QHBoxLayout()
        second_row.setSpacing(14)
        second_row.addStretch(1)
        second_row.addWidget(self.temperature_card, 2)
        second_row.addWidget(self.battery_card, 2)
        second_row.addStretch(1)
        metrics_rows.addLayout(first_row)
        metrics_rows.addLayout(second_row)
        layout.addLayout(metrics_rows)

        layout.addStretch(1)
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
        clear_button = QPushButton("Limpar logs")
        clear_button.setObjectName("clearLogsButton")
        clear_button.setToolTip("Remove os eventos do arquivo de log; o histórico de métricas permanece salvo.")
        clear_button.clicked.connect(self.confirm_clear_logs)
        toolbar.addWidget(clear_button)
        layout.addLayout(toolbar)

        self.log_viewer = QPlainTextEdit()
        self.log_viewer.setObjectName("logViewer")
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlaceholderText("Os eventos aparecerão aqui conforme o Syrixin os registrar.")
        self.log_viewer.setMaximumBlockCount(500)
        layout.addWidget(self.log_viewer, 1)
        return page

    def _create_hardware_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        labels = QVBoxLayout()
        labels.setSpacing(3)
        title = QLabel("Componentes detectados")
        title.setStyleSheet("font-size: 16px; font-weight: 650; color: #edf2f8;")
        self.hardware_status_label = QLabel(
            "Expanda um componente para ver seus sensores e leituras; os dados vêm do LibreHardwareMonitor."
        )
        self.hardware_status_label.setObjectName("subtitle")
        self.hardware_status_label.setWordWrap(True)
        labels.addWidget(title)
        labels.addWidget(self.hardware_status_label)
        toolbar.addLayout(labels)
        toolbar.addStretch(1)

        self.hardware_refresh_button = QPushButton("↻  Atualizar")
        self.hardware_refresh_button.setObjectName("refreshButton")
        self.hardware_refresh_button.clicked.connect(self.refresh_hardware)
        toolbar.addWidget(self.hardware_refresh_button)
        layout.addLayout(toolbar)

        self.hardware_search = QLineEdit()
        self.hardware_search.setObjectName("hardwareSearch")
        self.hardware_search.setPlaceholderText("⌕  Buscar componente ou sensor")
        self.hardware_search.textChanged.connect(self._filter_hardware)
        self.hardware_search.hide()
        layout.addWidget(self.hardware_search)

        self.hardware_empty_state = QLabel(
            "◈\n\nLibreHardwareMonitor não conectado\n\n"
            "Abra o LibreHardwareMonitor, ative Options → Remote Web Server → Run, "
            "e selecione Atualizar."
        )
        self.hardware_empty_state.setObjectName("hardwareEmptyState")
        self.hardware_empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hardware_empty_state.setWordWrap(True)
        layout.addWidget(self.hardware_empty_state, 1)

        self.hardware_tree = QTreeWidget()
        self.hardware_tree.setObjectName("hardwareTree")
        self.hardware_tree.setColumnCount(2)
        self.hardware_tree.setHeaderLabels(["Componente e sensor", "Leitura atual"])
        self.hardware_tree.setRootIsDecorated(True)
        self.hardware_tree.setAlternatingRowColors(False)
        self.hardware_tree.setUniformRowHeights(True)
        self.hardware_tree.setIndentation(20)
        self.hardware_tree.header().setStretchLastSection(False)
        self.hardware_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hardware_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.hardware_tree.hide()
        layout.addWidget(self.hardware_tree, 1)
        return page

    def _navigate_to_section(self, index):
        for button_index, button in enumerate(self.section_buttons):
            button.setChecked(button_index == index)

        if index == self.sections.currentIndex():
            return

        self.sections.setCurrentIndex(index)
        if index == self.hardware_tab_index:
            self.refresh_hardware()

    def refresh_hardware(self):
        self.hardware_refresh_button.setEnabled(False)
        self.hardware_status_label.setText("Consultando o LibreHardwareMonitor…")
        self.hardware_tree.clear()
        self._hardware_component_items = []
        try:
            components = get_hardware_inventory()
        except HardwareMonitorUnavailable:
            self.hardware_status_label.setText("Não foi possível obter os dados do hardware.")
            self.hardware_empty_state.setText(
                "◈\n\nLibreHardwareMonitor não conectado\n\n"
                "Abra o LibreHardwareMonitor, ative Options → Remote Web Server → Run, "
                "e selecione Atualizar."
            )
            self.hardware_tree.hide()
            self.hardware_search.hide()
            self.hardware_empty_state.show()
            return
        finally:
            self.hardware_refresh_button.setEnabled(True)

        if not components:
            self.hardware_status_label.setText("O monitor não retornou componentes detectados.")
            self.hardware_empty_state.setText(
                "◇\n\nNenhum componente encontrado\n\n"
                "Confira se os sensores de CPU, GPU, memória e armazenamento estão "
                "habilitados no LibreHardwareMonitor."
            )
            self.hardware_tree.hide()
            self.hardware_search.hide()
            self.hardware_empty_state.show()
            return

        total_sensors = 0
        for component in components:
            sensors = sorted(
                component["sensors"],
                key=lambda sensor: (
                    self._hardware_sensor_type_label(sensor["type"]),
                    sensor["name"].casefold(),
                ),
            )
            total_sensors += len(sensors)
            icon, category = self._hardware_category(component)
            component_item = QTreeWidgetItem([
                f"{icon}  {category} · {component['name']}",
                f"{len(sensors)} leituras",
            ])
            component_item.setToolTip(0, category)
            self.hardware_tree.addTopLevelItem(component_item)
            self._hardware_component_items.append(component_item)

            for sensor in sensors:
                sensor_item = QTreeWidgetItem([
                    f"{self._hardware_sensor_type_label(sensor['type'])} · {sensor['name']}",
                    self._format_hardware_sensor(sensor),
                ])
                component_item.addChild(sensor_item)

        self.hardware_status_label.setText(f"{len(components)} componentes · {total_sensors} leituras")
        self.hardware_empty_state.hide()
        self.hardware_search.show()
        self.hardware_tree.show()
        self._filter_hardware(self.hardware_search.text())

    @staticmethod
    def _hardware_category(component):
        identity = f"{component['name']} {component['identifier']}".casefold()
        categories = (
            (("intelcpu", "amdcpu", "processor", "ryzen", "core i", "xeon", "cpu"), "◉", "Processador"),
            (("gpu", "nvidia", "geforce", "radeon", "graphics", "intelgpu"), "▧", "Placa de vídeo"),
            (("ram", "memory"), "▤", "Memória"),
            (("nvme", "hdd", "ssd", "storage"), "▣", "Armazenamento"),
            (("motherboard", "mainboard", "superio", "nuvoton", "/lpc/"), "▦", "Placa-mãe"),
            (("network", "ethernet", "wifi", "nic"), "⌁", "Rede"),
        )
        for tokens, icon, category in categories:
            if any(token in identity for token in tokens):
                return icon, category
        return "◇", "Outro componente"

    @staticmethod
    def _hardware_sensor_type_label(sensor_type):
        labels = {
            "Temperature": "Temperatura",
            "Load": "Uso",
            "Fan": "Ventoinha",
            "Clock": "Frequência",
            "Frequency": "Frequência",
            "Power": "Potência",
            "Voltage": "Tensão",
            "Data": "Memória do dispositivo",
            "Throughput": "Transferência",
            "Level": "Nível",
            "Flow": "Fluxo",
        }
        return labels.get(sensor_type, sensor_type or "Sensor")

    def _filter_hardware(self, query):
        query = query.casefold().strip()
        for component_item in getattr(self, "_hardware_component_items", []):
            component_matches = query in component_item.text(0).casefold()
            has_matching_sensor = False
            for index in range(component_item.childCount()):
                sensor_item = component_item.child(index)
                sensor_matches = query in sensor_item.text(0).casefold()
                sensor_item.setHidden(bool(query) and not component_matches and not sensor_matches)
                has_matching_sensor = has_matching_sensor or sensor_matches
            component_item.setHidden(bool(query) and not component_matches and not has_matching_sensor)
            if query and (component_matches or has_matching_sensor):
                component_item.setExpanded(True)
            elif not query:
                component_item.setExpanded(False)

    @staticmethod
    def _format_hardware_sensor(sensor):
        value = sensor["value"]
        if value is None:
            return "N/A"
        if isinstance(value, (int, float)):
            units = {
                "Temperature": "°C",
                "Load": "%",
                "Fan": "RPM",
                "Clock": "MHz",
                "Frequency": "Hz",
                "Power": "W",
                "Voltage": "V",
                "Data": "B",
                "Throughput": "B/s",
            }
            unit = units.get(sensor["type"], "")
            digits = {"Fan": 0, "Clock": 0, "Voltage": 3}.get(sensor["type"], 1)
            if sensor["type"] == "Data" and value >= 1024 ** 3:
                return f"{value / (1024 ** 3):.1f} GB"
            return f"{value:.{digits}f} {unit}".strip()
        return str(value)

    def _create_ai_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.addStretch(1)

        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMaximumWidth(780)
        panel.setMinimumHeight(430)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(30, 28, 30, 30)
        panel_layout.setSpacing(14)

        eyebrow = QLabel("✦  PLANEJADO PARA UMA PRÓXIMA ETAPA")
        eyebrow.setStyleSheet("color: #55d6be; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        title = QLabel("Um assistente que entende o histórico do seu sistema")
        title.setWordWrap(True)
        title.setMinimumHeight(58)
        title.setStyleSheet("color: #f3f6fb; font-size: 22px; font-weight: 700;")
        description = QLabel(
            "A IA deverá transformar medições em explicações úteis, usando o histórico "
            "local para apontar padrões e ajudar no diagnóstico."
        )
        description.setWordWrap(True)
        description.setMinimumHeight(42)
        description.setStyleSheet("color: #aab4c4; font-size: 14px;")
        panel_layout.addWidget(eyebrow)
        panel_layout.addWidget(title)
        panel_layout.addWidget(description)

        ideas = QGridLayout()
        ideas.setHorizontalSpacing(12)
        ideas.setVerticalSpacing(12)
        for column in range(3):
            ideas.setColumnStretch(column, 1)
        for index, (name, detail) in enumerate((
            ("Encontrar padrões", "Ex.: picos de CPU que se repetem."),
            ("Explicar métricas", "Entender o que os números significam."),
            ("Sugerir otimizações", "Ações propostas para você revisar e autorizar."),
        )):
            idea = QFrame()
            idea.setMinimumHeight(96)
            idea.setStyleSheet("QFrame { background: #0c1119; border: 1px solid #202938; border-radius: 10px; }")
            idea_layout = QVBoxLayout(idea)
            idea_layout.setContentsMargins(14, 13, 14, 13)
            idea_layout.setSpacing(6)
            name_label = QLabel(name)
            name_label.setStyleSheet("color: #e7edf5; font-size: 13px; font-weight: 600;")
            detail_label = QLabel(detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet("color: #8993a5; font-size: 12px;")
            idea_layout.addWidget(name_label)
            idea_layout.addWidget(detail_label)
            ideas.addWidget(idea, index // 3, index % 3)
        panel_layout.addLayout(ideas)

        note = QLabel("Em breve")
        note.setWordWrap(True)
        note.setStyleSheet("color: #788497; font-size: 12px;")
        panel_layout.addWidget(note)

        layout.addWidget(panel, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        return page

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

    def confirm_clear_logs(self):
        answer = QMessageBox.question(
            self,
            "Limpar logs",
            "Isso apagará os eventos registrados pelo Syrixin. "
            "O histórico de métricas no banco de dados não será afetado. Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            clear_log_file()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Não foi possível limpar os logs",
                f"O arquivo de logs não pôde ser limpo: {error}",
            )
            return

        self.refresh_logs()

    def display_system_info(self, system):
        # A completed signal may already be queued when the window begins
        # closing. Ignore it before touching widgets or the SQLite connection.
        if self._is_closing:
            return

        self.status_label.setText("●  Monitoramento ativo")
        self.status_label.setStyleSheet("color: #71d9b6; font-size: 12px; font-weight: 600;")
        self.temperature_card.set_temperature(system.cpu_temp)
        self.update_metrics(
            format_cpu(system.cpu),
            format_ram(system.ram),
            format_disk(system.disk),
            format_battery(system.battery, system.battery_status),
            memory_percent=system.ram.percent if system.ram else None,
            disk_percent=system.disk.percent if system.disk else None,
            battery_percent=system.battery.percent if system.battery else None,
        )
        self._chart_samples.appendleft((None, system.cpu))
        self.cpu_card.set_visual_data(self._chart_samples)

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

    def update_metrics(
        self, cpu, memory, disk, battery,
        memory_percent=None, disk_percent=None, battery_percent=None,
    ):
        self.cpu_card.set_value(cpu)
        self.memory_card.set_value(memory)
        self.memory_card.set_visual_data(memory_percent)
        self.disk_card.set_value(disk)
        self.disk_card.set_visual_data(disk_percent)
        self.battery_card.set_value(battery)
        self.battery_card.set_visual_data(battery_percent)

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
    def __init__(self, icon, title, accent, value="--", visual=None):
        super().__init__()
        self.setObjectName("metricCard")
        self.setMinimumHeight(132)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(17, 14, 17, 15)
        card_layout.setSpacing(8)

        heading = QGridLayout()
        heading.setHorizontalSpacing(9)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #aab4c4; font-size: 13px; font-weight: 600;")
        self.visual_widget = None
        if visual in ("memory", "disk", "battery"):
            self.visual_widget = MetricLevelIndicator(accent, kind=visual)
            heading.addWidget(self.visual_widget, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            self.icon_label = QLabel(icon)
            self.icon_label.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: 700;")
            heading.addWidget(self.icon_label, 0, 0)
        heading.addWidget(self.title_label, 0, 1)
        heading.setColumnStretch(1, 1)
        card_layout.addLayout(heading)

        reading = QHBoxLayout()
        reading.setSpacing(10)
        self.value_label = QLabel(value)
        value_size = 19 if visual == "cpu" else 15
        self.value_label.setStyleSheet(
            f"color: #f3f6fb; font-size: {value_size}px; font-weight: 600;"
        )
        self.value_label.setWordWrap(True)
        reading.addWidget(self.value_label, 1)
        if visual == "cpu":
            self.visual_widget = CpuSparkline(accent)
            reading.addWidget(self.visual_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        card_layout.addLayout(reading, 1)
        card_layout.addStretch(1)

    def set_value(self, value):
        self.value_label.setText(str(value))

    def set_visual_data(self, value):
        if isinstance(self.visual_widget, CpuSparkline):
            self.visual_widget.update_data(value)
        elif isinstance(self.visual_widget, MetricLevelIndicator):
            self.visual_widget.set_value(value)


class TemperatureCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("metricCard")
        self.setMinimumHeight(112)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 14, 17, 15)
        layout.setSpacing(6)

        title = QLabel("Temperatura da CPU")
        title.setStyleSheet("color: #aab4c4; font-size: 13px; font-weight: 600;")
        layout.addWidget(title)

        reading = QHBoxLayout()
        reading.setSpacing(13)
        self.indicator = TemperatureIndicator()
        reading.addWidget(self.indicator, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.value_label = QLabel("N/A")
        self.value_label.setStyleSheet("color: #f3f6fb; font-size: 22px; font-weight: 650;")
        reading.addWidget(self.value_label)
        reading.addStretch(1)
        layout.addLayout(reading)

    def set_temperature(self, value):
        self.value_label.setText(format_temperature(value))
        self.indicator.set_temperature(value)


def main():
    app = QApplication(sys.argv)
    window = SyrixinWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
