from PyQt6.QtWidgets import QTabWidget

from app.ui.views.workspace_components import WorkspaceViewFactory


class WorkspaceWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        bundle = WorkspaceViewFactory().build()
        self.scene = bundle.scene
        self.view = bundle.view
        self.addTab(self.view, "Network schematic")
