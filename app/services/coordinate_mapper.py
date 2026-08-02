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


def pdf_font_size_to_screen(font_size: float, geometry: RenderGeometry) -> float:
    """Converte pontos do PDF para pixels do pixmap renderizado."""
    if geometry.zoom <= 0:
        raise ValueError("Zoom deve ser maior que zero.")
    return font_size * geometry.zoom


def synchronized_scroll_value(
    value: int,
    source_minimum: int,
    source_maximum: int,
    target_minimum: int,
    target_maximum: int,
) -> int:
    """Converte uma posição de rolagem para o intervalo de outro painel."""
    source_span = source_maximum - source_minimum
    target_span = target_maximum - target_minimum
    if source_span <= 0 or target_span <= 0:
        return target_minimum
    progress = (value - source_minimum) / source_span
    return round(target_minimum + progress * target_span)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
