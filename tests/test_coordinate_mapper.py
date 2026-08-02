from app.services.coordinate_mapper import (
    RenderGeometry,
    pdf_font_size_to_screen,
    pdf_to_screen,
    screen_to_pdf,
    synchronized_scroll_value,
)


def test_screen_to_pdf_accounts_for_zoom() -> None:
    geometry = RenderGeometry(
        zoom=2.0,
        image_width=1200,
        image_height=1600,
        page_width=600.0,
        page_height=800.0,
    )

    assert screen_to_pdf(300, 500, geometry) == (150.0, 250.0)


def test_pdf_to_screen_accounts_for_zoom() -> None:
    geometry = RenderGeometry(
        zoom=1.5,
        image_width=900,
        image_height=1200,
        page_width=600.0,
        page_height=800.0,
    )

    assert pdf_to_screen(100, 200, geometry) == (150.0, 300.0)


def test_screen_to_pdf_clamps_to_page_bounds() -> None:
    geometry = RenderGeometry(
        zoom=2.0,
        image_width=1200,
        image_height=1600,
        page_width=600.0,
        page_height=800.0,
    )

    assert screen_to_pdf(5000, -20, geometry) == (600.0, 0.0)


def test_pdf_font_size_scales_with_zoom_like_the_rendered_pixmap() -> None:
    geometry = RenderGeometry(
        zoom=1.5,
        image_width=900,
        image_height=1200,
        page_width=600.0,
        page_height=800.0,
    )

    assert pdf_font_size_to_screen(12, geometry) == 18.0


def test_synchronized_scroll_value_preserves_relative_position() -> None:
    assert synchronized_scroll_value(25, 0, 100, 0, 200) == 50
    assert synchronized_scroll_value(100, 0, 100, 10, 210) == 210
    assert synchronized_scroll_value(25, 0, 0, 10, 210) == 10
