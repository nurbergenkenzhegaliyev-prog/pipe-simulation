from PyQt6.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QToolBar, QFrame, QLabel
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QActionGroup
from PyQt6.QtWidgets import QStyle
from app.ui.tool_palette import Tool


class TopTabsWidget(QTabWidget):
    tool_changed = pyqtSignal(object)
    run_clicked = pyqtSignal()
    results_clicked = pyqtSignal()
    open_clicked = pyqtSignal()
    save_as_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    new_clicked = pyqtSignal()

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

        home_tab = QWidget()
        home_tab.setObjectName("RibbonPage")
        home_layout = QHBoxLayout(home_tab)
        home_layout.setContentsMargins(6, 4, 6, 6)
        home_layout.setSpacing(6)

        file_group, file_toolbar = self._create_toolbar_group("File")
        new_action = file_toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), "New"
        )
        open_action = file_toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open"
        )
        save_action = file_toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save As"
        )
        import_action = file_toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Import JSON"
        )

        run_group, run_toolbar = self._create_toolbar_group("Run")
        run_action = run_toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Run"
        )
        results_action = run_toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView), "Results"
        )

        self._mark_inactive_action(file_toolbar, new_action)

        home_layout.addWidget(file_group)
        home_layout.addWidget(self._create_vertical_divider())
        home_layout.addWidget(run_group)
        home_layout.addStretch(1)

        insert_tab = QWidget()
        insert_tab.setObjectName("RibbonPage")
        insert_layout = QHBoxLayout(insert_tab)
        insert_layout.setContentsMargins(6, 4, 6, 6)
        insert_layout.setSpacing(6)

        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        boundary_group, boundary_toolbar = self._create_toolbar_group("Boundary nodes")
        self._add_tool_action(
            boundary_toolbar, tool_group, "Source", Tool.SOURCE, QStyle.StandardPixmap.SP_DialogYesButton
        )
        self._add_tool_action(
            boundary_toolbar, tool_group, "Sink", Tool.SINK, QStyle.StandardPixmap.SP_DialogNoButton
        )

        internal_group, internal_toolbar = self._create_toolbar_group("Internal nodes")
        self._add_tool_action(
            internal_toolbar, tool_group, "Node", Tool.NODE, QStyle.StandardPixmap.SP_DirIcon
        )

        connections_group, connections_toolbar = self._create_toolbar_group("Connections")
        self._add_tool_action(
            connections_toolbar, tool_group, "Pipe", Tool.PIPE, QStyle.StandardPixmap.SP_LineEditClearButton
        )

        equipment_group, equipment_toolbar = self._create_toolbar_group("Equipment")
        self._add_tool_action(
            equipment_toolbar, tool_group, "Pump", Tool.PUMP, QStyle.StandardPixmap.SP_ArrowUp
        )
        self._add_tool_action(
            equipment_toolbar, tool_group, "Valve", Tool.VALVE, QStyle.StandardPixmap.SP_ArrowDown
        )

        other_group, other_toolbar = self._create_toolbar_group("Others")
        self._add_tool_action(
            other_toolbar, tool_group, "Select", Tool.SELECT, QStyle.StandardPixmap.SP_ArrowRight, True
        )

        insert_layout.addWidget(boundary_group)
        insert_layout.addWidget(self._create_vertical_divider())
        insert_layout.addWidget(internal_group)
        insert_layout.addWidget(self._create_vertical_divider())
        insert_layout.addWidget(connections_group)
        insert_layout.addWidget(self._create_vertical_divider())
        insert_layout.addWidget(equipment_group)
        insert_layout.addWidget(self._create_vertical_divider())
        insert_layout.addWidget(other_group)
        insert_layout.addStretch(1)

        self.addTab(home_tab, "Home")
        self.addTab(insert_tab, "Insert")

        self.setStyleSheet(
            self.styleSheet()
            + "QWidget#RibbonPage { background: #f7f7f7; border: 1px solid #cfcfcf; }"
        )

        new_action.triggered.connect(self.new_clicked)
        open_action.triggered.connect(self.open_clicked)
        save_action.triggered.connect(self.save_as_clicked)
        import_action.triggered.connect(self.import_clicked)
        run_action.triggered.connect(self.run_clicked)
        results_action.triggered.connect(self.results_clicked)

    def _create_toolbar_group(self, title):
        container = QFrame()
        container.setFrameShape(QFrame.Shape.NoFrame)
        container.setStyleSheet("QFrame { background: transparent; border: none; }")
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setStyleSheet(
            "QToolBar { background: transparent; border: none; }"
            "QToolButton { padding: 4px 8px; }"
        )

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet("QLabel { font-weight: 600; color: #3a3a3a; border: none; }")

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)
        container_layout.addWidget(toolbar)
        container_layout.addWidget(label)
        container.setLayout(container_layout)
        return container, toolbar

    def _create_vertical_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setLineWidth(1)
        divider.setStyleSheet(
            "QFrame { color: #f7f7f7; background: #cfcfcf; margin-top: 6px; margin-bottom: 6px; }"
        )
        return divider

    def _add_tool_action(self, toolbar, group, text, tool, icon, checked=False):
        action = toolbar.addAction(self.style().standardIcon(icon), text)
        action.setCheckable(True)
        action.setChecked(checked)
        group.addAction(action)
        action.triggered.connect(lambda _checked, t=tool: self.tool_changed.emit(t))
        return action

    def _mark_inactive_action(self, toolbar, action):
        button = toolbar.widgetForAction(action)
        if button is None:
            return
        button.setStyleSheet("QToolButton { color: #b00000; background: #ffe6e6; }")
        button.setToolTip("Not implemented yet.")
