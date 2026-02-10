"""
Pytest configuration and fixtures for the test suite.

Provides shared fixtures for Qt application setup and common test utilities.
"""

import pytest
from PyQt6.QtWidgets import QApplication
import sys


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests that need Qt."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="function")
def qapp_func(qapp):
    """Provide QApplication instance for function-scoped tests."""
    yield qapp
    # Process events to clean up
    qapp.processEvents()
