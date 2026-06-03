from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea

from app.models.project import Point
from app.services.coordinate_mapper import RenderGeometry, pdf_to_screen, screen_to_pdf


class PdfCanvas(QLabel):
    clicked = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setMouseTracking(True)
        self._base_pixmap: QPixmap | None = None
        self._geometry: RenderGeometry | None = None
        self._points: dict[str, Point] = {}

    def set_page(self, pixmap: QPixmap, geometry: RenderGeometry, points: dict[str, Point]) -> None:
        self._base_pixmap = pixmap
        self._geometry = geometry
        self._points = points
        self._redraw()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._geometry is None:
            return
        position = event.position()
        x = position.x()
        y = position.y()
        if x < 0 or y < 0 or x > self.width() or y > self.height():
            return
        pdf_x, pdf_y = screen_to_pdf(x, y, self._geometry)
        self.clicked.emit(pdf_x, pdf_y)

    def _redraw(self) -> None:
        if self._base_pixmap is None or self._geometry is None:
            return
        pixmap = QPixmap(self._base_pixmap)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#d62828"), 2)
        painter.setPen(pen)
        painter.setBrush(QColor(214, 40, 40, 170))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        for index, (name, point) in enumerate(self._points.items(), start=1):
            x, y = pdf_to_screen(point.x, point.y, self._geometry)
            center = QPoint(round(x), round(y))
            painter.drawEllipse(center, 6, 6)
            painter.drawLine(center.x() - 10, center.y(), center.x() + 10, center.y())
            painter.drawLine(center.x(), center.y() - 10, center.x(), center.y() + 10)
            label = str(index) if len(name) > 18 else name
            painter.drawText(center.x() + 10, center.y() - 8, label)
        painter.end()
        self.setPixmap(pixmap)
        self.resize(pixmap.size())


class PdfViewer(QScrollArea):
    clicked = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self.canvas = PdfCanvas()
        self.canvas.clicked.connect(self.clicked.emit)
        self.setWidget(self.canvas)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_page(self, pixmap: QPixmap, geometry: RenderGeometry, points: dict[str, Point]) -> None:
        self.canvas.set_page(pixmap, geometry, points)
