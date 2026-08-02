from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.gui.file_dialogs import get_save_file_name
from app.gui.point_editor import PointEditor
from app.gui.pdf_viewer import OverlayMode, PdfViewer
from app.models.project import Point, Project
from app.services.coordinate_mapper import synchronized_scroll_value
from app.services.json_store import JsonStore
from app.services.pdf_renderer import PdfRenderer
from app.utils.paths import open_folder


class MainWindow(QMainWindow):
    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project
        self.store = JsonStore()
        self.renderer = PdfRenderer(project.pdf_path)
        self.current_page = 0
        self.zoom = 1.5
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(350)
        self._autosave_timer.timeout.connect(self.save_project)

        self.real_viewer = PdfViewer(OverlayMode.REAL)
        self.preview_viewer = PdfViewer(OverlayMode.PREVIEW)
        self.real_viewer.clicked.connect(self.capture_point)
        self.point_editors: dict[str, PointEditor] = {}

        self.setWindowTitle("PDF Coordinate Mapper")
        self.resize(1200, 650)
        self._build_toolbar()
        self._build_layout()
        self.refresh_page()

    def _build_layout(self) -> None:
        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        self.points_editor_layout = QVBoxLayout()
        self.points_editor_layout.setContentsMargins(2, 2, 2, 2)
        self.points_editor_layout.setSpacing(2)
        self.points_editor_layout.addStretch()
        self.points_editor_widget = QWidget()
        self.points_editor_widget.setLayout(self.points_editor_layout)
        self.points_scroll = QScrollArea()
        self.points_scroll.setWidgetResizable(True)
        self.points_scroll.setWidget(self.points_editor_widget)
        side.addWidget(self.points_scroll)

        viewers = QSplitter(Qt.Orientation.Horizontal)
        viewers.setChildrenCollapsible(False)
        viewers.addWidget(self._viewer_panel("Real", self.real_viewer))
        viewers.addWidget(self._viewer_panel("Preview", self.preview_viewer))
        viewers.setStretchFactor(0, 1)
        viewers.setStretchFactor(1, 1)
        viewers.setSizes([1, 1])
        self._synchronize_scrollbars()

        main = QHBoxLayout()
        main.addWidget(viewers, 1)
        side_widget = QWidget()
        side_widget.setLayout(side)
        side_widget.setFixedWidth(370)
        main.addWidget(side_widget)

        container = QWidget()
        container.setLayout(main)
        self.setCentralWidget(container)

    @staticmethod
    def _viewer_panel(title: str, viewer: PdfViewer) -> QWidget:
        label = QLabel(title)
        label.setStyleSheet("text-align: left; font-weight: bold; padding: 0 4px;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(label)
        layout.addWidget(viewer, 1)
        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _synchronize_scrollbars(self) -> None:
        self._link_scrollbars(
            self.real_viewer.horizontalScrollBar(), self.preview_viewer.horizontalScrollBar()
        )
        self._link_scrollbars(
            self.real_viewer.verticalScrollBar(), self.preview_viewer.verticalScrollBar()
        )

    @staticmethod
    def _link_scrollbars(first, second) -> None:
        def transfer(value: int, source, target) -> None:
            target_value = synchronized_scroll_value(
                value,
                source.minimum(),
                source.maximum(),
                target.minimum(),
                target.maximum(),
            )
            with QSignalBlocker(target):
                target.setValue(target_value)

        def sync_to_second(value: int) -> None:
            transfer(value, first, second)

        def sync_to_first(value: int) -> None:
            transfer(value, second, first)

        def resync_from_first(*_) -> None:
            QTimer.singleShot(0, lambda: sync_to_second(first.value()))

        def resync_from_second(*_) -> None:
            QTimer.singleShot(0, lambda: sync_to_first(second.value()))

        first.valueChanged.connect(sync_to_second)
        second.valueChanged.connect(sync_to_first)
        first.rangeChanged.connect(resync_from_first)
        second.rangeChanged.connect(resync_from_second)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Ferramentas", self)
        self.addToolBar(toolbar)
        actions = [
            ("Página anterior", QKeySequence("PgUp"), self.previous_page),
            ("Próxima página", QKeySequence("PgDown"), self.next_page),
            ("Zoom +", QKeySequence.StandardKey.ZoomIn, self.zoom_in),
            ("Zoom -", QKeySequence.StandardKey.ZoomOut, self.zoom_out),
            ("Salvar JSON", QKeySequence.StandardKey.Save, self.save_project),
            ("Abrir pasta do JSON", None, lambda: open_folder(Path(self.project.json_path))),
            ("Exportar resumo", None, self.export_summary),
            ("Sair", QKeySequence("Esc"), self.close),
        ]
        for text, shortcut, callback in actions:
            action = QAction(text, self)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(callback)
            toolbar.addAction(action)

    def refresh_page(self) -> None:
        pixmap, geometry = self.renderer.render_page(self.current_page, self.zoom)
        page_points = {
            name: point
            for name, point in self.project.points.items()
            if point.page == self.current_page
        }
        self.real_viewer.set_page(pixmap, geometry, page_points)
        self.preview_viewer.set_page(pixmap, geometry, page_points)
        self._rebuild_point_editors(page_points)
        self.statusBar().showMessage(
            f"Projeto: {self.project.project_name} | PDF: {Path(self.project.pdf_path).name} | "
            f"Página {self.current_page + 1}/{self.renderer.page_count} | Zoom {self.zoom:.2f}x"
        )

    def capture_point(self, x: float, y: float) -> None:
        name = self._next_point_name()
        point = Point(page=self.current_page, page_label=self.current_page + 1, x=x, y=y)
        self.project.add_point(name, point)
        self.refresh_page()
        self._schedule_save()
        self.point_editors[name].focus_name()

    def _rebuild_point_editors(self, page_points: dict[str, Point]) -> None:
        while self.points_editor_layout.count() > 1:
            item = self.points_editor_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.point_editors.clear()

        page_size = self.project.page_sizes[self.current_page]
        for name, point in page_points.items():
            editor = PointEditor(name, point.x, point.y, page_size.width, page_size.height)
            editor.remove_requested.connect(self.remove_point)
            editor.name_changed.connect(self.rename_point_inline)
            editor.name_editing_finished.connect(self.finish_renaming_point)
            editor.coordinates_changed.connect(self.update_point_coordinates)
            self.points_editor_layout.insertWidget(self.points_editor_layout.count() - 1, editor)
            self.point_editors[name] = editor

    def _next_point_name(self) -> str:
        index = 1
        while f"ponto_{index}" in self.project.points:
            index += 1
        return f"ponto_{index}"

    def rename_point_inline(self, old_name: str, new_name: str) -> None:
        editor = self.point_editors.get(old_name)
        if editor is None or new_name == old_name:
            editor and editor.set_name_error(False)
            return
        if not new_name or new_name in self.project.points:
            editor.set_name_error(True)
            return
        self.project.rename_point(old_name, new_name)
        editor.set_point_name(new_name)
        self.point_editors.pop(old_name)
        self.point_editors[new_name] = editor
        self._refresh_overlays()
        self._schedule_save()

    def finish_renaming_point(self, name: str) -> None:
        editor = self.point_editors.get(name)
        if editor is not None and editor.name_input.text().strip() != name:
            editor.restore_valid_name()

    def update_point_coordinates(self, name: str, x: float, y: float) -> None:
        point = self.project.points.get(name)
        if point is None:
            return
        self.project.update_point(
            name,
            Point(page=point.page, page_label=point.page_label, x=x, y=y),
        )
        self._refresh_overlays()
        self._schedule_save()

    def remove_point(self, name: str) -> None:
        if name not in self.project.points:
            return
        self.project.remove_point(name)
        self._refresh_overlays()
        editor = self.point_editors.pop(name, None)
        if editor is not None:
            editor.deleteLater()
        self._schedule_save()

    def _refresh_overlays(self) -> None:
        page_points = {
            name: point
            for name, point in self.project.points.items()
            if point.page == self.current_page
        }
        self.real_viewer.set_points(page_points)
        self.preview_viewer.set_points(page_points)

    def _schedule_save(self) -> None:
        self._autosave_timer.start()

    def previous_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_page()

    def next_page(self) -> None:
        if self.current_page + 1 < self.renderer.page_count:
            self.current_page += 1
            self.refresh_page()

    def zoom_in(self) -> None:
        self.zoom = min(self.zoom + 0.25, 5.0)
        self.refresh_page()

    def zoom_out(self) -> None:
        self.zoom = max(self.zoom - 0.25, 0.5)
        self.refresh_page()

    def save_project(self) -> None:
        self.store.save(self.project)
        self.statusBar().showMessage(f"JSON salvo em {self.project.json_path}", 4000)

    def export_summary(self) -> None:
        default = str(Path(self.project.json_path).with_suffix(".md"))
        file_name, _ = get_save_file_name(self, "Exportar resumo", "Markdown (*.md);;Texto (*.txt)", default)
        if not file_name:
            return
        lines = [
            f"# {self.project.project_name}",
            "",
            f"- PDF: {self.project.pdf_path}",
            f"- Páginas: {self.project.page_count}",
            f"- Sistema de coordenadas: PyMuPDF PDF points",
            "",
            "## Pontos",
            "",
        ]
        for name, point in self.project.points.items():
            lines.append(f"- {name}: página {point.page_label}, x={point.x:.2f}, y={point.y:.2f}")
        Path(file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        QMessageBox.information(self, "Resumo exportado", f"Resumo salvo em:\n{file_name}")

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._autosave_timer.isActive():
            self._autosave_timer.stop()
            self.save_project()
        self.renderer.close()
        super().closeEvent(event)
