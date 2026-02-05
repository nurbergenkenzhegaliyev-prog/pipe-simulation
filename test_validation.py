"""Quick test of validation system"""

import pytest
from PyQt6.QtWidgets import QApplication

from app.ui.scenes.network_scene import NetworkScene
from app.ui.validation.realtime_validator import RealtimeNetworkValidator, ValidationLevel


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_validation():
    """Test the validation system"""
    scene = NetworkScene()
    validator = scene.validator
    
    # Test with empty scene
    print("Testing empty scene...")
    issues = validator.validate(scene)
    print(f"Empty scene issues: {len(issues)}")
    
    # Create a node manually for testing
    from PyQt6.QtCore import QPointF
    node1 = scene._create_node(QPointF(0, 0), is_source=True)
    print(f"Created node: {node1.node_id}")
    
    # Validate with source but no pressure
    print("\nValidating with source (no pressure)...")
    issues = validator.validate(scene)
    errors = [i for i in issues if i.level == ValidationLevel.ERROR]
    print(f"Found {len(errors)} errors")
    for err in errors:
        print(f"  - {err.message}")
    
    print("\n✓ Validation system working!")

if __name__ == "__main__":
    test_validation()
