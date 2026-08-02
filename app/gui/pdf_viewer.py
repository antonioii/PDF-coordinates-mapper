from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea

from app.models.project import Point
from app.services.coordinate_mapper import (
    RenderGeometry,
    pdf_font_size_to_screen,
    pdf_to_screen,
    screen_to_pdf,
)


PREVIEW_TEXT = "X"
PREVIEW_FONT_FAMILY = "Arial"
PREVIEW_FONT_SIZE_PDF = 12
PREVIEW_COLOR = "#ff0000"


class OverlayMode(StrEnum):
    REAL = "real"
    PREVIEW = "preview"


class PdfCanvas(QLabel):
    clicked = Signal(float, float)

    def __init__(self, overlay_mode: OverlayMode, accepts_clicks: bool) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setMouseTracking(True)
        self._base_pixmap: QPixmap | None = None
        self._geometry: RenderGeometry | None = None
        self._points: dict[str, Point] = {}
        self._overlay_mode = overlay_mode
        self._accepts_clicks = accepts_clicks

    def set_page(self, pixmap: QPixmap, geometry: RenderGeometry, points: dict[str, Point]) -> None:
        # Cada canvas mantém uma cópia independente antes de desenhar overlays.
        self._base_pixmap = QPixmap(pixmap)
        self._geometry = geometry
        self.set_points(points)

    def set_points(self, points: dict[str, Point]) -> None:
        """Redesenha apenas os overlays, sem renderizar o PDF novamente."""
        self._points = points
        self._redraw()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if (
            not self._accepts_clicks
            or event.button() != Qt.MouseButton.LeftButton
            or self._geometry is None
        ):
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
        if self._overlay_mode == OverlayMode.REAL:
            self._draw_real_markers(painter)
        else:
            self._draw_preview_stamps(painter)
        painter.end()
        self.setPixmap(pixmap)
        self.resize(pixmap.size())

    def _draw_real_markers(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#d62828"), 2))
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

    def _draw_preview_stamps(self, painter: QPainter) -> None:
        """Usa a coordenada PDF como origem esquerda da linha de base do texto."""
        painter.setPen(QPen(QColor(PREVIEW_COLOR)))
        font = QFont(PREVIEW_FONT_FAMILY)
        font.setPixelSize(max(1, round(pdf_font_size_to_screen(PREVIEW_FONT_SIZE_PDF, self._geometry))))
        painter.setFont(font)
        for point in self._points.values():
            x, y = pdf_to_screen(point.x, point.y, self._geometry)
            painter.drawText(QPointF(x, y), PREVIEW_TEXT)


class PdfViewer(QScrollArea):
    clicked = Signal(float, float)

    def __init__(self, overlay_mode: OverlayMode = OverlayMode.REAL) -> None:
        super().__init__()
        self.canvas = PdfCanvas(
            overlay_mode=overlay_mode,
            accepts_clicks=overlay_mode == OverlayMode.REAL,
        )
        self.canvas.clicked.connect(self.clicked.emit)
        self.setWidget(self.canvas)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_page(self, pixmap: QPixmap, geometry: RenderGeometry, points: dict[str, Point]) -> None:
        self.canvas.set_page(pixmap, geometry, points)

    def set_points(self, points: dict[str, Point]) -> None:
        self.canvas.set_points(points)
