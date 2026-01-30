from enum import Enum, auto

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QToolButton, QButtonGroup)


class Tool(Enum):
    SELECT = auto()
    NODE = auto()
    PIPE = auto()
    SOURCE = auto()
    SINK = auto()
    PUMP = auto()
    VALVE = auto()


class ToolPalette(QWidget):
    tool_changed = pyqtSignal(object)  # emits Tool

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Instruments")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        # Add tool buttons
        self._add_tool_button("Select", Tool.SELECT, checked=True, layout=layout)
        self._add_tool_button("Node", Tool.NODE, layout=layout)
        self._add_tool_button("Pipe", Tool.PIPE, layout=layout)
        self._add_tool_button("Source", Tool.SOURCE, layout=layout)
        self._add_tool_button("Sink", Tool.SINK, layout=layout)

        layout.addStretch(1)

        self._group.buttonClicked.connect(self._on_clicked)

    def _add_tool_button(self, text: str, tool: Tool, layout: QVBoxLayout, checked: bool = False):
        btn = QToolButton()
        btn.setText(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setMinimumHeight(34)

        # store the tool on the button
        btn.setProperty("tool", tool)

        self._group.addButton(btn)
        layout.addWidget(btn)

    def _on_clicked(self, button: QToolButton):
        tool = button.property("tool")
        self.tool_changed.emit(tool)
