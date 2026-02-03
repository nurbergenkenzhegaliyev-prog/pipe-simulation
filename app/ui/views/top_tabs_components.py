from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolBar, QVBoxLayout, QWidget, QStyle

from app.ui.tooling.tool_types import Tool


class ToolbarGroupFactory:
    def __init__(self, owner: QWidget):
        self._owner = owner

    def create_group(self, title: str) -> tuple[QFrame, QToolBar]:
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

    def create_divider(self) -> QFrame:
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setLineWidth(1)
        divider.setStyleSheet(
            "QFrame { color: #f7f7f7; background: #cfcfcf; margin-top: 6px; margin-bottom: 6px; }"
        )
        return divider

    def add_tool_action(
        self,
        toolbar: QToolBar,
        group: QActionGroup,
        text: str,
        tool: Tool,
        icon: QStyle.StandardPixmap,
        checked: bool = False,
    ) -> QAction:
        action = toolbar.addAction(self._owner.style().standardIcon(icon), text)
        action.setCheckable(True)
        action.setChecked(checked)
        group.addAction(action)
        action.triggered.connect(lambda _checked, t=tool: self._owner.tool_changed.emit(t))
        return action

    @staticmethod
    def mark_inactive_action(toolbar: QToolBar, action: QAction) -> None:
        button = toolbar.widgetForAction(action)
        if button is None:
            return
        button.setStyleSheet("QToolButton { color: #b00000; background: #ffe6e6; }")
        button.setToolTip("Not implemented yet.")


@dataclass
class HomeTabActions:
    new_action: QAction
    open_action: QAction
    save_action: QAction
    import_action: QAction
    run_action: QAction
    results_action: QAction
    fluid_action: QAction


class HomeTabBuilder:
    def __init__(self, owner: QWidget, groups: ToolbarGroupFactory):
        self._owner = owner
        self._groups = groups

    def build(self) -> tuple[QWidget, HomeTabActions]:
        home_tab = QWidget()
        home_tab.setObjectName("RibbonPage")
        home_layout = QHBoxLayout(home_tab)
        home_layout.setContentsMargins(6, 4, 6, 6)
        home_layout.setSpacing(6)

        file_group, file_toolbar = self._groups.create_group("File")
        new_action = file_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), "New"
        )
        open_action = file_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open"
        )
        save_action = file_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save As"
        )
        import_action = file_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Import JSON"
        )

        run_group, run_toolbar = self._groups.create_group("Run")
        run_action = run_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Run"
        )
        results_action = run_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView), "Results"
        )

        settings_group, settings_toolbar = self._groups.create_group("Settings")
        fluid_action = settings_toolbar.addAction(
            self._owner.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView), "Fluid"
        )

        self._groups.mark_inactive_action(file_toolbar, new_action)

        home_layout.addWidget(file_group)
        home_layout.addWidget(self._groups.create_divider())
        home_layout.addWidget(run_group)
        home_layout.addWidget(self._groups.create_divider())
        home_layout.addWidget(settings_group)
        home_layout.addStretch(1)

        return home_tab, HomeTabActions(
            new_action=new_action,
            open_action=open_action,
            save_action=save_action,
            import_action=import_action,
            run_action=run_action,
            results_action=results_action,
            fluid_action=fluid_action,
        )


class InsertTabBuilder:
    def __init__(self, owner: QWidget, groups: ToolbarGroupFactory):
        self._owner = owner
        self._groups = groups

    def build(self) -> QWidget:
        insert_tab = QWidget()
        insert_tab.setObjectName("RibbonPage")
        insert_layout = QHBoxLayout(insert_tab)
        insert_layout.setContentsMargins(6, 4, 6, 6)
        insert_layout.setSpacing(6)

        tool_group = QActionGroup(self._owner)
        tool_group.setExclusive(True)

        boundary_group, boundary_toolbar = self._groups.create_group("Boundary nodes")
        self._groups.add_tool_action(
            boundary_toolbar, tool_group, "Source", Tool.SOURCE, QStyle.StandardPixmap.SP_DialogYesButton
        )
        self._groups.add_tool_action(
            boundary_toolbar, tool_group, "Sink", Tool.SINK, QStyle.StandardPixmap.SP_DialogNoButton
        )

        internal_group, internal_toolbar = self._groups.create_group("Internal nodes")
        self._groups.add_tool_action(
            internal_toolbar, tool_group, "Node", Tool.NODE, QStyle.StandardPixmap.SP_DirIcon
        )

        connections_group, connections_toolbar = self._groups.create_group("Connections")
        self._groups.add_tool_action(
            connections_toolbar, tool_group, "Pipe", Tool.PIPE, QStyle.StandardPixmap.SP_LineEditClearButton
        )

        equipment_group, equipment_toolbar = self._groups.create_group("Equipment")
        self._groups.add_tool_action(
            equipment_toolbar, tool_group, "Pump", Tool.PUMP, QStyle.StandardPixmap.SP_ArrowUp
        )
        self._groups.add_tool_action(
            equipment_toolbar, tool_group, "Valve", Tool.VALVE, QStyle.StandardPixmap.SP_ArrowDown
        )

        other_group, other_toolbar = self._groups.create_group("Others")
        self._groups.add_tool_action(
            other_toolbar, tool_group, "Select", Tool.SELECT, QStyle.StandardPixmap.SP_ArrowRight, True
        )

        insert_layout.addWidget(boundary_group)
        insert_layout.addWidget(self._groups.create_divider())
        insert_layout.addWidget(internal_group)
        insert_layout.addWidget(self._groups.create_divider())
        insert_layout.addWidget(connections_group)
        insert_layout.addWidget(self._groups.create_divider())
        insert_layout.addWidget(equipment_group)
        insert_layout.addWidget(self._groups.create_divider())
        insert_layout.addWidget(other_group)
        insert_layout.addStretch(1)

        return insert_tab
