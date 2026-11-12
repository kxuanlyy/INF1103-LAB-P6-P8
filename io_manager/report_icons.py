"""Small, theme-aware line icons for Qt rich-text reports."""

import re

from PySide6.QtCore import QByteArray, Qt, QUrl
from PySide6.QtGui import QImage, QPainter, QTextDocument
from PySide6.QtSvg import QSvgRenderer


_PATHS = {
    "summary": '<path d="M4 4v16h16M8 15v-4m5 4V7m5 8v-6"/>',
    "accepted": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "rejected": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>',
    "warning": '<path d="m12 3 10 18H2L12 3Zm0 5v6m0 3v.5"/>',
    "folder": '<path d="M3 7V5h7l2 3h9v12H3V7Z"/>',
    "book": '<path d="M12 5v15M3 4h5q4 0 4 3 0-3 4-3h5v15h-5q-4 0-4 2 0-2-4-2H3Z"/>',
    "ingredients": '<path d="m3 6 1 1 2-2m3 1h12M3 12h2m4 0h12M3 18h2m4 0h12"/>',
    "steps": '<path d="M13 4H4v16h16v-9M10 14l1-4 8-8 3 3-8 8-4 1Z"/>',
    "recipe": '<path d="M4 3v6q0 3 3 3t3-3V3M7 3v18M19 3q-5 4-5 10h5m0-10v18"/>',
}


def register_report_icons(editor, html, dark):
    """Register crisp 2x images; HTML sets their logical size to 16px."""
    for name in set(re.findall(r"foodrescue-icon:([a-z]+)", html)) & _PATHS.keys():
        colors = {
            "accepted": "#b0cfbc" if dark else "#36634d",
            "rejected": "#dcaaa9" if dark else "#943f42",
            "warning": "#cfbc97" if dark else "#74591e",
        }
        color = colors.get(name, "#b9c6bf" if dark else "#58655e")
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{_PATHS[name]}</svg>'
        )
        image = QImage(32, 32, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        QSvgRenderer(QByteArray(svg.encode())).render(painter)
        painter.end()
        editor.document().addResource(QTextDocument.ImageResource, QUrl(f"foodrescue-icon:{name}"), image)
