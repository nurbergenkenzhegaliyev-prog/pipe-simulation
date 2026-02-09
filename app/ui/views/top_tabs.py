from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import pyqtSignal

from app.ui.views.top_tabs_components import HomeTabBuilder, InsertTabBuilder, ToolbarGroupFactory


class TopTabsWidget(QTabWidget):
    tool_changed = pyqtSignal(object)
    run_clicked = pyqtSignal()
    results_clicked = pyqtSignal()
    open_clicked = pyqtSignal()
    save_as_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    import_epanet_clicked = pyqtSignal()
    new_clicked = pyqtSignal()
    fluid_settings_clicked = pyqtSignal()
    simulation_settings_clicked = pyqtSignal()
    transient_simulation_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setStyleSheet(
            "QTabWidget::pane { border-top: 1px solid #cfcfcf; }"
            "QTabBar::tab { height: 26px; padding: 4px 16px; font-weight: 600; "
            "color: #2f2f2f; background: #f4f4f4; border: 1px solid #cfcfcf; "
            "border-bottom: none; }"
            "QTabBar::tab:selected { background: #0b71c7; color: #ffffff; }"
            "QTabBar::tab:!selected { margin-top: 2px; }"
        )

        groups = ToolbarGroupFactory(self)
        home_tab, home_actions = HomeTabBuilder(self, groups).build()
        insert_tab, self._tool_group = InsertTabBuilder(self, groups).build()

        self.addTab(home_tab, "Home")
        self.addTab(insert_tab, "Insert")

        self.setStyleSheet(
            self.styleSheet()
            + "QWidget#RibbonPage { background: #f7f7f7; border: 1px solid #cfcfcf; }"
        )

        home_actions.new_action.triggered.connect(self.new_clicked)
        home_actions.open_action.triggered.connect(self.open_clicked)
        home_actions.save_action.triggered.connect(self.save_as_clicked)
        home_actions.import_action.triggered.connect(self.import_clicked)
        home_actions.import_epanet_action.triggered.connect(self.import_epanet_clicked)
        home_actions.run_action.triggered.connect(self.run_clicked)
        home_actions.results_action.triggered.connect(self.results_clicked)
        home_actions.fluid_action.triggered.connect(self.fluid_settings_clicked)
        home_actions.simulation_settings_action.triggered.connect(self.simulation_settings_clicked)
        home_actions.transient_action.triggered.connect(self.transient_simulation_clicked)
