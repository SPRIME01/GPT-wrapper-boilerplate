"""
Pytest configuration for the test suite.
"""
import sys
import os
from pathlib import Path
import pytest

# Add the project root directory to the Python path
# This allows absolute imports starting with "backend"
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))  # Use insert(0, ...) instead of append to prioritize this path

print(f"Added path to sys.path: {root_dir}")
print(f"Current sys.path: {sys.path}")

# This helps pytest find the packages
pytest.register_assert_rewrite('backend.tests')

# Add a dummy fixture to verify conftest is loaded
@pytest.fixture(scope="session", autouse=True)
def verify_imports():
    """Verify that the imports are working correctly."""
    print("conftest.py loaded successfully!")
    return True
