from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QButtonGroup, QLabel, QToolButton, QVBoxLayout, QWidget

from app.ui.tooling.tool_types import Tool


@dataclass
class ToolButtonSpec:
    text: str
    tool: Tool
    checked: bool = False


class ToolPaletteBuilder:
    def build(self, parent: QWidget, specs: Iterable[ToolButtonSpec]) -> tuple[QVBoxLayout, QButtonGroup]:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Instruments")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        group = QButtonGroup(parent)
        group.setExclusive(True)

        for spec in specs:
            button = QToolButton()
            button.setText(spec.text)
            button.setCheckable(True)
            button.setChecked(spec.checked)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setMinimumHeight(34)
            button.setProperty("tool", spec.tool)

            group.addButton(button)
            layout.addWidget(button)

        layout.addStretch(1)
        return layout, group
