import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def create_app():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)

    app = QApplication(sys.argv)
    app.setApplicationName("My App")
    return app
