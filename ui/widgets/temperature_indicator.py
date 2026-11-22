from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget


class TemperatureIndicator(QWidget):
    """Draw a thermometer whose fill and color follow the live CPU reading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 62)
        self._display_temperature = 20.0
        self._has_reading = False
        self._animation = QPropertyAnimation(self, b"displayTemperature", self)
        self._animation.setDuration(450)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_temperature(self, value):
        if value is None:
            self._animation.stop()
            self._has_reading = False
            self.update()
            return

        target = max(20.0, min(float(value), 100.0))
        self._has_reading = True
        self._animation.stop()
        self._animation.setStartValue(self._display_temperature)
        self._animation.setEndValue(target)
        self._animation.start()

    def _get_display_temperature(self):
        return self._display_temperature

    def _set_display_temperature(self, value):
        self._display_temperature = value
        self.update()

    displayTemperature = Property(float, _get_display_temperature, _set_display_temperature)

    @staticmethod
    def _color_for_temperature(value):
        if value < 40:
            return QColor("#54b7ff")
        if value < 55:
            return QColor("#55d6be")
        if value < 70:
            return QColor("#b8d86e")
        if value < 80:
            return QColor("#f2c45b")
        if value < 90:
            return QColor("#ff9f6e")
        return QColor("#ff5c6c")

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        tube_top = 5.0
        tube_bottom = self.height() - 19.0
        bulb_center = QPointF(center_x, self.height() - 12.0)
        color = self._color_for_temperature(self._display_temperature)
        if not self._has_reading:
            color = QColor("#566174")

        if self._has_reading:
            glow = QRadialGradient(bulb_center, 17.0)
            glow_color = QColor(color)
            glow_color.setAlpha(65)
            glow.setColorAt(0.0, glow_color)
            glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QRectF(center_x - 17, bulb_center.y() - 17, 34, 34))

        tube_width = 12.0
        tube_rect = QRectF(center_x - tube_width / 2, tube_top, tube_width, tube_bottom - tube_top)
        painter.setPen(QPen(QColor("#465164"), 2.0))
        painter.setBrush(QColor("#111923"))
        painter.drawRoundedRect(tube_rect, tube_width / 2, tube_width / 2)

        bulb_radius = 10.0
        painter.setPen(QPen(QColor("#465164"), 2.0))
        painter.setBrush(QColor("#111923"))
        painter.drawEllipse(bulb_center, bulb_radius, bulb_radius)

        if self._has_reading:
            fraction = (self._display_temperature - 20.0) / 80.0
            fill_top = tube_bottom - fraction * (tube_bottom - tube_top - 5.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(
                QRectF(center_x - 3.0, fill_top, 6.0, tube_bottom - fill_top + 5.0),
                3.0,
                3.0,
            )
            painter.drawEllipse(bulb_center, 7.0, 7.0)

        painter.setPen(QPen(QColor("#6d7788"), 1.0))
        for y in (tube_top + 13, tube_top + 25, tube_top + 37):
            painter.drawLine(int(center_x + 8), int(y), int(center_x + 12), int(y))

        painter.end()
