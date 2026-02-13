from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from app.ui.views.workspace_components import WorkspaceViewFactory


class WorkspaceWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        bundle = WorkspaceViewFactory().build()
        self.scene = bundle.scene
        self.view = bundle.view
        self._gis_view = None
        self.addTab(self.view, "Network schematic")

    def show_gis_tab(self) -> None:
        if self._gis_view is None:
            self._gis_view = QWebEngineView(self)
            self._gis_view.setUrl(QUrl("https://www.arcgis.com/apps/mapviewer/index.html"))
            self.addTab(self._gis_view, "ArcGIS")
        self.setCurrentWidget(self._gis_view)
