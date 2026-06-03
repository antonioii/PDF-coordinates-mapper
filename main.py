from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.gui.file_dialogs import get_open_file_name
from app.gui.main_window import MainWindow
from app.gui.startup_dialog import StartupDialog
from app.models.project import Project
from app.services.json_store import JsonStore
from app.services.pdf_renderer import PdfRenderer


def build_project_from_startup(values: dict[str, str]) -> Project | None:
    store = JsonStore()
    if values["mode"] == "existing":
        project = store.load(values["json_path"])
        pdf_path = Path(project.pdf_path)
        if not pdf_path.exists():
            file_name, _ = get_open_file_name(None, "PDF não encontrado. Selecione o PDF", "PDF (*.pdf)")
            if not file_name:
                return None
            project.pdf_path = file_name
        renderer = PdfRenderer(project.pdf_path)
        project.page_count = renderer.page_count
        project.page_sizes = renderer.page_sizes()
        renderer.close()
        return project

    renderer = PdfRenderer(values["pdf_path"])
    project = Project.new(
        project_name=values["project_name"],
        pdf_path=values["pdf_path"],
        json_path=values["json_path"],
        page_count=renderer.page_count,
        page_sizes=renderer.page_sizes(),
    )
    renderer.close()
    if Path(project.json_path).exists():
        existing = store.load(project.json_path)
        project.points = existing.points
        project.created_at = existing.created_at
        store.save(project, create_backup=True)
    else:
        store.create_empty(project)
    return project


def main() -> int:
    app = QApplication(sys.argv)
    startup = StartupDialog()
    if startup.exec() != QDialog.DialogCode.Accepted:
        return 0
    try:
        project = build_project_from_startup(startup.values())
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(None, "Erro ao abrir projeto", str(exc))
        return 1
    if project is None:
        return 0
    window = MainWindow(project)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
