@echo off
REM Activate virtual environment
call .venv\Scripts\activate

REM Install or reinstall key packages
uv pip install pytest pytest-asyncio httpx fastapi strawberry-graphql dependency-injector

echo Dependencies installed. You should now be able to run tests.
