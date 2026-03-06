@echo off
setlocal

echo ================================
echo Activating virtual environment...
echo ================================
call ".venv\Scripts\activate"

echo.
echo ================================
echo Running test1_module...
echo ================================
python -m tests.test1_module

echo.
echo ================================
echo Running Search & Filter tests...
echo ================================
python -m tests.test_search_filter

echo.
echo ================================
echo Running Simple Visualizer tests...
echo ================================
python -m tests.test_simple_visualizer

echo.
echo ================================
echo Running Block Visualizer tests...
echo ================================
python -m tests.test_block_visualizer

echo.
echo ================================
echo Running Workspace Manager tests...
echo ================================
python -m tests.test_workspace_manager

echo.
echo ================================
echo Running Facade and CLI tests...
echo ================================
python -m tests.test_facade_cli

echo.
echo ================================
echo Tests complete!
echo ================================
pause
