@echo off
REM Activate virtual environment
call .venv\Scripts\activate

REM Run tests with proper Python path
python -m pytest tests/infrastructure-layer/test_graphql_resolvers.py tests/infrastructure-layer/test_rest_controllers.py -v

echo Tests completed.
