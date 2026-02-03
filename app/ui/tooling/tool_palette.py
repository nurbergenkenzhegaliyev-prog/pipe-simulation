from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QToolButton

from app.ui.tooling.tool_palette_components import ToolButtonSpec, ToolPaletteBuilder
from app.ui.tooling.tool_types import Tool


class ToolPalette(QWidget):
    tool_changed = pyqtSignal(object)  # emits Tool

    def __init__(self, parent=None):
        super().__init__(parent)

        specs = [
            ToolButtonSpec("Select", Tool.SELECT, checked=True),
            ToolButtonSpec("Node", Tool.NODE),
            ToolButtonSpec("Pipe", Tool.PIPE),
            ToolButtonSpec("Source", Tool.SOURCE),
            ToolButtonSpec("Sink", Tool.SINK),
        ]
        _, self._group = ToolPaletteBuilder().build(self, specs)

        self._group.buttonClicked.connect(self._on_clicked)

    def _on_clicked(self, button: QToolButton):
        tool = button.property("tool")
        self.tool_changed.emit(tool)
