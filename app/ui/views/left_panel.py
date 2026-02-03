from PyQt6.QtWidgets import QTabWidget

from app.ui.views.left_panel_components import LeftPanelBuilder, SceneTreeRefresher


class LeftPanelWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setStyleSheet(
            "QTabWidget::pane { border-top: 1px solid #cfcfcf; }"
            "QTabBar::tab { height: 24px; padding: 4px 12px; font-weight: 600; }"
            "QTabBar::tab:selected { background: #f2f2f2; }"
        )

        builder = LeftPanelBuilder()
        inputs_widget, state = builder.build_inputs_tab()
        tasks_widget = builder.build_tasks_tab()

        self._state = state
        self._refresher = SceneTreeRefresher(state)

        self.addTab(inputs_widget, "Inputs")
        self.addTab(tasks_widget, "Tasks")

    def refresh_from_scene(self, scene):
        self._refresher.refresh(scene)
