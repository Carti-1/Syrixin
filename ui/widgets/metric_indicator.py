"""Animated compact level indicator for memory, disk, and battery cards."""

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class MetricLevelIndicator(QWidget):
    def __init__(self, accent, kind, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 40)
        self._accent = QColor(accent)
        self._kind = kind
        self._level = 0.0
        self._has_value = False
        self._animation = QPropertyAnimation(self, b"level", self)
        self._animation.setDuration(360)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_value(self, value):
        if value is None:
            self._animation.stop()
            self._has_value = False
            self.update()
            return
        try:
            target = max(0.0, min(float(value), 100.0))
        except (TypeError, ValueError):
            self._has_value = False
            self.update()
            return

        self._has_value = True
        self._animation.stop()
        self._animation.setStartValue(self._level)
        self._animation.setEndValue(target)
        self._animation.start()

    def _get_level(self):
        return self._level

    def _set_level(self, value):
        self._level = value
        self.update()

    level = Property(float, _get_level, _set_level)

    def _level_color(self):
        if not self._has_value:
            return QColor("#566174")
        if self._kind == "battery":
            if self._level <= 20:
                return QColor("#ff5c6c")
            if self._level <= 40:
                return QColor("#ffad66")
            if self._level <= 65:
                return QColor("#f2c45b")
            return QColor("#55d6be")
        if self._level >= 90:
            return QColor("#ff5c6c")
        if self._level >= 75:
            return QColor("#ff9f6e")
        if self._level >= 50:
            return QColor("#f2c45b")
        return self._accent

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = self._level_color()
        fill_ratio = self._level / 100.0 if self._has_value else 0.0
        painter.setPen(QPen(QColor("#344052"), 1.3))
        painter.setBrush(QColor("#151d29"))

        if self._kind == "memory":
            outline = QPainterPath()
            outline.moveTo(4, 7)
            outline.lineTo(56, 7)
            outline.lineTo(56, 27)
            outline.lineTo(39, 27)
            outline.lineTo(36, 32)
            outline.lineTo(31, 32)
            outline.lineTo(28, 27)
            outline.lineTo(4, 27)
            outline.closeSubpath()
            painter.drawPath(outline)
            painter.save()
            painter.setClipPath(outline)
            painter.fillRect(
                QRectF(5, 8, 50 * fill_ratio, 18), color
            )
            painter.restore()
            painter.setPen(QPen(QColor("#516074"), 1.0))
            for x in (10, 23, 37, 49):
                painter.drawRoundedRect(QRectF(x, 11, 7, 11), 1.5, 1.5)
            painter.setPen(QPen(QColor("#a98b58"), 1.4))
            for x in (9, 17, 25, 39, 47, 55):
                painter.drawLine(x, 28, x, 34)

        elif self._kind == "disk":
            body = QRectF(4, 5, 52, 30)
            painter.drawRoundedRect(body, 5, 5)
            painter.save()
            painter.setClipRect(QRectF(7, 8, 46, 24))
            painter.fillRect(QRectF(7, 8, 46 * fill_ratio, 24), color)
            painter.restore()
            painter.setPen(QPen(QColor("#758197"), 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(9, 10, 3, 3))
            painter.drawEllipse(QRectF(48, 27, 3, 3))
            painter.setPen(QPen(QColor("#eef3fa"), 1.0))
            painter.drawText(QRectF(17, 11, 31, 17), Qt.AlignmentFlag.AlignCenter, "SSD")

        elif self._kind == "battery":
            body = QRectF(4, 8, 48, 25)
            terminal = QRectF(52, 15, 5, 11)
            painter.drawRoundedRect(body, 4, 4)
            painter.drawRoundedRect(terminal, 1.5, 1.5)
            painter.save()
            painter.setClipRect(QRectF(7, 11, 42, 19))
            painter.fillRect(QRectF(7, 11, 42 * fill_ratio, 19), color)
            painter.restore()

        painter.end()
