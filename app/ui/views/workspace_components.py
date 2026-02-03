from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QGraphicsView

from app.ui.scenes.network_scene import NetworkScene


@dataclass
class WorkspaceViewBundle:
    scene: NetworkScene
    view: QGraphicsView


class WorkspaceViewFactory:
    def build(self) -> WorkspaceViewBundle:
        scene = NetworkScene()
        view = QGraphicsView(scene)
        view.setRenderHint(view.renderHints().Antialiasing)
        view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        return WorkspaceViewBundle(scene=scene, view=view)
