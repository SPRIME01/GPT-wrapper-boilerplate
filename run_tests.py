#!/usr/bin/env python
"""
Test runner for GPT-wrapper-boilerplate.
This script automates running tests with proper environment setup.
"""
import os
import sys
import subprocess

def main():
    """Run tests with proper environment setup."""
    # Determine the virtual environment Python executable
    if sys.platform.startswith('win'):
        python_path = os.path.join('.venv', 'Scripts', 'python.exe')
    else:
        python_path = os.path.join('.venv', 'bin', 'python')

    # Check if it exists
    if not os.path.exists(python_path):
        print(f"Error: Virtual environment Python not found at {python_path}")
        print("Make sure to create and activate your virtual environment first.")
        return 1

    # Run tests
    test_command = [
        python_path,
        "-m",
        "pytest",
        "tests/infrastructure-layer/test_graphql_resolvers.py",
        "tests/infrastructure-layer/test_rest_controllers.py",
        "-v"
    ]

    print(f"Running tests with: {' '.join(test_command)}")
    result = subprocess.run(test_command)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
