from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.gui.file_dialogs import get_save_file_name
from app.gui.pdf_viewer import PdfViewer
from app.gui.point_dialog import PointDialog
from app.models.project import Point, Project
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

        self.viewer = PdfViewer()
        self.viewer.clicked.connect(self.capture_point)
        self.points_list = QListWidget()
        self.points_list.itemDoubleClicked.connect(lambda _: self.rename_selected_point())

        self.setWindowTitle("PDF Coordinate Mapper")
        self.resize(1180, 820)
        self._build_toolbar()
        self._build_layout()
        self.refresh_page()

    def _build_layout(self) -> None:
        remove_button = QPushButton("Remover ponto")
        remove_button.clicked.connect(self.remove_selected_point)
        rename_button = QPushButton("Renomear ponto")
        rename_button.clicked.connect(self.rename_selected_point)

        side = QVBoxLayout()
        side.addWidget(self.points_list)
        side.addWidget(rename_button)
        side.addWidget(remove_button)

        main = QHBoxLayout()
        main.addWidget(self.viewer, 1)
        side_widget = QWidget()
        side_widget.setLayout(side)
        side_widget.setFixedWidth(280)
        main.addWidget(side_widget)

        container = QWidget()
        container.setLayout(main)
        self.setCentralWidget(container)

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
        self.viewer.set_page(pixmap, geometry, page_points)
        self.points_list.clear()
        for name, point in page_points.items():
            self.points_list.addItem(f"{name} | x={point.x:.2f}, y={point.y:.2f}")
        self.statusBar().showMessage(
            f"Projeto: {self.project.project_name} | PDF: {Path(self.project.pdf_path).name} | "
            f"Página {self.current_page + 1}/{self.renderer.page_count} | Zoom {self.zoom:.2f}x"
        )

    def capture_point(self, x: float, y: float) -> None:
        dialog = PointDialog(self.current_page, x, y, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name = dialog.point_name()
        if not name:
            QMessageBox.warning(self, "Nome vazio", "Informe um nome para o ponto.")
            return
        point = Point(page=self.current_page, page_label=self.current_page + 1, x=x, y=y)
        self.add_point_with_duplicate_handling(name, point)

    def add_point_with_duplicate_handling(self, name: str, point: Point) -> None:
        if name not in self.project.points:
            self.project.add_point(name, point)
            self.save_project()
            self.refresh_page()
            return
        choice = QMessageBox.question(
            self,
            "Nome já existe",
            "Já existe um ponto com esse nome. Deseja sobrescrever apenas esse ponto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.No,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.project.add_point(name, point, overwrite=True)
            self.save_project()
            self.refresh_page()
        elif choice == QMessageBox.StandardButton.No:
            new_name, ok = QInputDialog.getText(self, "Salvar com outro nome", "Novo nome do ponto:")
            if ok and new_name.strip():
                self.add_point_with_duplicate_handling(new_name.strip(), point)

    def selected_point_name(self) -> str | None:
        item = self.points_list.currentItem()
        if item is None:
            return None
        return item.text().split(" | ", 1)[0]

    def remove_selected_point(self) -> None:
        name = self.selected_point_name()
        if not name:
            return
        choice = QMessageBox.question(self, "Remover ponto", f"Remover '{name}'?")
        if choice == QMessageBox.StandardButton.Yes:
            self.project.remove_point(name)
            self.save_project()
            self.refresh_page()

    def rename_selected_point(self) -> None:
        old_name = self.selected_point_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, "Renomear ponto", "Novo nome:", text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        overwrite = False
        if new_name.strip() in self.project.points:
            choice = QMessageBox.question(
                self,
                "Nome já existe",
                "Já existe um ponto com esse nome. Sobrescrever esse ponto?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            overwrite = choice == QMessageBox.StandardButton.Yes
            if not overwrite:
                return
        self.project.rename_point(old_name, new_name.strip(), overwrite=overwrite)
        self.save_project()
        self.refresh_page()

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
        self.renderer.close()
        super().closeEvent(event)
