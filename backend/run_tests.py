#!/usr/bin/env python
"""
Test runner script for GPT-wrapper-boilerplate using Python 3.12.

This script ensures tests are run with the correct Python 3.12 interpreter
from the activated virtual environment, avoiding path-related issues.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the specified test files using pytest with the correct Python version."""
    # Get the current Python executable (which should be from the activated venv)
    python_executable = sys.executable

    # Verify Python version
    python_version = sys.version_info
    print(f"Using Python {python_version.major}.{python_version.minor}.{python_version.micro}")

    if python_version.major != 3 or python_version.minor != 12:
        print(f"WARNING: Expected Python 3.12.x but found {python_version.major}.{python_version.minor}.{python_version.micro}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Test execution cancelled")
            return 1

    # Construct the test command using the current Python interpreter
    test_files = [
        "tests/infrastructure-layer/test_graphql_resolvers.py",
        "tests/infrastructure-layer/test_rest_controllers.py"
    ]

    cmd = [python_executable, "-m", "pytest"] + test_files + ["-v"]

    # Print information about the execution
    print(f"Running tests with Python: {python_executable}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)

    # Run the tests
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Run the tests
    sys.exit(run_tests())
