from PyQt6.QtWidgets import QWidget

from app.ui.views.results_view_components import ResultsTableBuilder, ResultsUpdater, ResultsViewLayout
from app.services.pressure_drop_service import PressureDropService
from app.services.pipe_point_analyzer import PipePointAnalyzer


class ResultsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tables = ResultsTableBuilder().build(self)
        ResultsViewLayout(self, self._tables)
        self._updater = ResultsUpdater()
        self._pipe_analyzer = None

    def set_pipe_analyzer(self, analyzer: PipePointAnalyzer):
        """Set the pipe analyzer for multi-point analysis"""
        self._pipe_analyzer = analyzer
        self._updater._pipe_analyzer = analyzer

    def update_results(self, network):
        self._updater.set_dependencies(network, self._pipe_analyzer)
        self._updater.update(self._tables, network)
