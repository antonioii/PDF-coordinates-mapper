from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class PointEditor(QWidget):
    """Linha compacta para editar um ponto sem abrir diálogos modais."""

    remove_requested = Signal(str)
    name_changed = Signal(str, str)
    name_editing_finished = Signal(str)
    coordinates_changed = Signal(str, float, float)

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        maximum_x: float,
        maximum_y: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._name = name

        self.remove_button = QPushButton("×", self)
        self.remove_button.setObjectName("removePointButton")
        self.remove_button.setToolTip("Remover ponto")
        self.remove_button.setFixedWidth(24)
        self.remove_button.setStyleSheet("color: #d62828; font-weight: bold;")

        self.name_input = QLineEdit(name, self)
        self.name_input.setPlaceholderText("Nome do ponto")
        self.name_input.setMinimumWidth(90)
        self.name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.x_input = self._coordinate_input(x, maximum_x)
        self.x_input.setPrefix("x=")
        self.x_input.setToolTip("Coordenada X no PDF")
        self.y_input = self._coordinate_input(y, maximum_y)
        self.y_input.setPrefix("y=")
        self.y_input.setToolTip("Coordenada Y no PDF")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)
        layout.addWidget(self.remove_button)
        layout.addWidget(self.name_input, 1)
        layout.addWidget(self.x_input)
        layout.addWidget(self.y_input)

        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self._name))
        self.name_input.textChanged.connect(self._emit_name_change)
        self.name_input.editingFinished.connect(lambda: self.name_editing_finished.emit(self._name))
        self.x_input.valueChanged.connect(self._emit_coordinates_change)
        self.y_input.valueChanged.connect(self._emit_coordinates_change)

    @staticmethod
    def _coordinate_input(value: float, maximum: float) -> QDoubleSpinBox:
        input_widget = QDoubleSpinBox()
        input_widget.setDecimals(2)
        input_widget.setSingleStep(1.0)
        input_widget.setRange(0.0, max(0.0, maximum))
        input_widget.setValue(value)
        input_widget.setFixedWidth(84)
        return input_widget

    @property
    def point_name(self) -> str:
        return self._name

    def set_point_name(self, name: str) -> None:
        self._name = name
        with QSignalBlocker(self.name_input):
            self.name_input.setText(name)
        self.set_name_error(False)

    def restore_valid_name(self) -> None:
        self.set_point_name(self._name)

    def set_name_error(self, has_error: bool) -> None:
        self.name_input.setStyleSheet(
            "border: 1px solid #d62828;" if has_error else ""
        )

    def focus_name(self) -> None:
        self.name_input.setFocus()
        self.name_input.selectAll()

    def _emit_name_change(self, text: str) -> None:
        self.name_changed.emit(self._name, text.strip())

    def _emit_coordinates_change(self) -> None:
        self.coordinates_changed.emit(self._name, self.x_input.value(), self.y_input.value())
