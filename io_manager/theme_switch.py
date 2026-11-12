"""A compact theme switch with native checkbox keyboard/accessibility behavior."""

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox

from io_manager.main_window_style import is_dark


class ThemeSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(54, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Dark mode")
        self._position = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(160)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._animation.valueChanged.connect(self._move_thumb)
        self.toggled.connect(self._animate)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(float(checked))
        self._animation.start()

    def _move_thumb(self, position):
        self._position = position
        self.update()

    def hitButton(self, position):
        return self.rect().contains(position)

    def paintEvent(self, event):
        # QSS cannot position an animated checkbox thumb; paint just this control.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        track = "#478a63" if self.isChecked() else ("#50565a" if is_dark(self) else "#cbd0d4")
        painter.setBrush(QColor(track if self.isEnabled() else "#a4aaa6"))
        painter.drawRoundedRect(QRectF(3, 3, 48, 26), 13, 13)
        thumb_x = 5 + 22 * self._position
        painter.setBrush(QColor(0, 0, 0, 28))
        painter.drawEllipse(QRectF(thumb_x, 6, 22, 22))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(thumb_x, 5, 22, 22))
        if self.hasFocus():
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor("#a7cbb6" if is_dark(self) else "#36634d"), 1.5))
            painter.drawRoundedRect(QRectF(1, 1, 52, 30), 15, 15)
