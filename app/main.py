from app.core import create_app
from app.ui import MainWindow


def main():
    app = create_app()
    window = MainWindow()
    window.show()
    app.exec()
