from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class PointDialog(QDialog):
    def __init__(self, page: int, x: float, y: float, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Salvar ponto")
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Nome do ponto")

        details = QLabel(f"Página: {page + 1}\nX: {x:.2f}\nY: {y:.2f}", self)
        form = QFormLayout()
        form.addRow("Nome do ponto", self.name_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(details)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def point_name(self) -> str:
        return self.name_input.text().strip()
