from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.gui.file_dialogs import get_open_file_name, get_save_file_name


class StartupDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PDF Coordinate Mapper")
        self.resize(560, 220)
        self.mode = "new"

        title = QLabel("PDF Coordinate Mapper", self)
        title.setStyleSheet("font-size: 22px; font-weight: 700;")

        self.pdf_input = QLineEdit(self)
        self.project_input = QLineEdit(self)
        self.json_input = QLineEdit(self)

        select_pdf = QPushButton("Selecionar PDF", self)
        select_pdf.clicked.connect(self.select_pdf)
        select_json = QPushButton("Escolher local do JSON", self)
        select_json.clicked.connect(self.select_json)
        open_project = QPushButton("Abrir projeto existente", self)
        open_project.clicked.connect(self.open_existing)
        start = QPushButton("Iniciar mapeamento", self)
        start.clicked.connect(self.start_new)

        pdf_row = QHBoxLayout()
        pdf_row.addWidget(self.pdf_input)
        pdf_row.addWidget(select_pdf)

        json_row = QHBoxLayout()
        json_row.addWidget(self.json_input)
        json_row.addWidget(select_json)

        form = QFormLayout()
        form.addRow("PDF", pdf_row)
        form.addRow("Nome do projeto", self.project_input)
        form.addRow("JSON", json_row)

        actions = QHBoxLayout()
        actions.addWidget(open_project)
        actions.addStretch()
        actions.addWidget(start)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(actions)

    def select_pdf(self) -> None:
        file_name, _ = get_open_file_name(self, "Selecionar PDF", "PDF (*.pdf)")
        if file_name:
            self.pdf_input.setText(file_name)
            if not self.project_input.text().strip():
                self.project_input.setText(Path(file_name).stem)

    def select_json(self) -> None:
        file_name, _ = get_save_file_name(self, "Salvar JSON", "JSON (*.json)")
        if file_name:
            if not file_name.lower().endswith(".json"):
                file_name += ".json"
            self.json_input.setText(file_name)

    def start_new(self) -> None:
        if not self.pdf_input.text().strip() or not self.project_input.text().strip() or not self.json_input.text().strip():
            QMessageBox.warning(self, "Dados incompletos", "Informe PDF, nome do projeto e local do JSON.")
            return
        self.mode = "new"
        self.accept()

    def open_existing(self) -> None:
        file_name, _ = get_open_file_name(self, "Abrir projeto", "JSON (*.json)")
        if file_name:
            self.json_input.setText(file_name)
            self.mode = "existing"
            self.accept()

    def values(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "pdf_path": self.pdf_input.text().strip(),
            "project_name": self.project_input.text().strip(),
            "json_path": self.json_input.text().strip(),
        }
