from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPalette, QPainter, QPolygon
from PySide6.QtWidgets import QComboBox as BaseComboBox


# Draw the dropdown arrow using the current theme colours.
class QComboBox(BaseComboBox):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().color(QPalette.Text))
        center_x = self.width() - 11
        center_y = self.height() // 2
        painter.drawPolygon(QPolygon([
            QPoint(center_x - 4, center_y - 2),
            QPoint(center_x + 4, center_y - 2),
            QPoint(center_x, center_y + 3),
        ]))
