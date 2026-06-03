from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderGeometry:
    zoom: float
    image_width: int
    image_height: int
    page_width: float
    page_height: float


def screen_to_pdf(x: float, y: float, geometry: RenderGeometry) -> tuple[float, float]:
    if geometry.zoom <= 0:
        raise ValueError("Zoom deve ser maior que zero.")
    pdf_x = x / geometry.zoom
    pdf_y = y / geometry.zoom
    return _clamp(pdf_x, 0.0, geometry.page_width), _clamp(pdf_y, 0.0, geometry.page_height)


def pdf_to_screen(x: float, y: float, geometry: RenderGeometry) -> tuple[float, float]:
    if geometry.zoom <= 0:
        raise ValueError("Zoom deve ser maior que zero.")
    return x * geometry.zoom, y * geometry.zoom


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
