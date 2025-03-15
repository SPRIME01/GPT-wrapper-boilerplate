@echo off
REM Activate the virtual environment
call .venv\Scripts\activate

REM Verify Python and pytest are working
python --version
pytest --version

echo Environment activated. You can now run tests.
