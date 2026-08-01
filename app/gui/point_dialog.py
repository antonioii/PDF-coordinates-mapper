from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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


class PointEditDialog(QDialog):
    """Edita o nome e as coordenadas de um ponto já salvo."""

    def __init__(self, name: str, x: float, y: float, page: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Editar ponto")
        self.name_input = QLineEdit(name, self)
        self.x_input = self._coordinate_input(x)
        self.y_input = self._coordinate_input(y)

        form = QFormLayout()
        form.addRow("Página", QLabel(str(page + 1), self))
        form.addRow("Nome do ponto", self.name_input)
        form.addRow("X", self.x_input)
        form.addRow("Y", self.y_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @staticmethod
    def _coordinate_input(value: float) -> QDoubleSpinBox:
        input_widget = QDoubleSpinBox()
        input_widget.setDecimals(2)
        input_widget.setRange(0.0, max(1_000_000.0, value))
        input_widget.setValue(value)
        return input_widget

    def values(self) -> tuple[str, float, float]:
        return self.name_input.text().strip(), self.x_input.value(), self.y_input.value()
