from __future__ import annotations

from pathlib import Path

import fitz
from PySide6.QtGui import QImage, QPixmap

from app.models.project import PdfPageSize
from app.services.coordinate_mapper import RenderGeometry


class PdfRenderer:
    def __init__(self, pdf_path: str | Path) -> None:
        self.path = Path(pdf_path)
        self.document = fitz.open(self.path)

    @property
    def page_count(self) -> int:
        return self.document.page_count

    def page_sizes(self) -> list[PdfPageSize]:
        sizes: list[PdfPageSize] = []
        for index in range(self.page_count):
            rect = self.document.load_page(index).rect
            sizes.append(PdfPageSize(page=index, width=rect.width, height=rect.height))
        return sizes

    def render_page(self, page_index: int, zoom: float) -> tuple[QPixmap, RenderGeometry]:
        page = self.document.load_page(page_index)
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = QImage(
            pixmap.samples,
            pixmap.width,
            pixmap.height,
            pixmap.stride,
            QImage.Format.Format_RGB888,
        ).copy()
        geometry = RenderGeometry(
            zoom=zoom,
            image_width=pixmap.width,
            image_height=pixmap.height,
            page_width=page.rect.width,
            page_height=page.rect.height,
        )
        return QPixmap.fromImage(image), geometry

    def close(self) -> None:
        self.document.close()
