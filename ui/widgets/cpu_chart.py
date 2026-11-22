"""Small, lightweight CPU history graph for the overview card."""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class CpuSparkline(QWidget):
    """Draw recent CPU samples without axes or labels, like a compact sparkline."""

    def __init__(self, accent="#55d6be", parent=None):
        super().__init__(parent)
        self.setFixedSize(92, 48)
        self._accent = accent
        self._values = []

    def update_data(self, rows):
        values = []
        for row in reversed(list(rows or [])):
            value = row[1] if len(row) > 1 else None
            if value is not None:
                values.append(max(0.0, min(float(value), 100.0)))
        self._values = values[-60:]
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bounds = self.rect().adjusted(2, 4, -2, -4)
        baseline = bounds.bottom()
        painter.setPen(QPen(QColor("#27303e"), 1))
        painter.drawLine(int(bounds.left()), int(baseline), int(bounds.right()), int(baseline))

        if not self._values:
            painter.end()
            return

        value = self._values[-1]
        color = QColor(self._accent)
        if value >= 85:
            color = QColor("#ff5c6c")
        elif value >= 70:
            color = QColor("#ff9f6e")
        elif value >= 50:
            color = QColor("#f2c45b")

        points = []
        vertical_range = max(1.0, bounds.height() - 4)
        denominator = max(1, len(self._values) - 1)
        for index, sample in enumerate(self._values):
            x = bounds.left() + bounds.width() * index / denominator
            y = bounds.bottom() - vertical_range * sample / 100.0
            points.append(QPointF(x, y))

        line = QPainterPath(points[0])
        for point in points[1:]:
            line.lineTo(point)
        painter.setPen(QPen(color, 2.2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(line)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(points[-1], 3.0, 3.0)
        painter.end()
