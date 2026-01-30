import os
import sys

# # ---- REQUIRED for QtWebEngine on Windows ----
# os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
# os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"

from PyQt6 import QtWebEngineWidgets  # noqa: F401
# IMPORTANT: import WebEngine BEFORE QApplication

from app.main import main

if __name__ == "__main__":
    main()
