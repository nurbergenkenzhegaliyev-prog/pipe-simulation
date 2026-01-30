from PyQt6.QtWidgets import QTabWidget, QGraphicsView
from app.ui.network_scene import NetworkScene


class WorkspaceWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = NetworkScene()

        view = QGraphicsView(self.scene)
        view.setRenderHint(view.renderHints().Antialiasing)
        view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view = view

        self.addTab(view, "Network schematic")
