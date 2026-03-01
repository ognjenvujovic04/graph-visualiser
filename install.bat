@echo off
setlocal

echo ================================
echo Creating virtual environment (.venv)...
echo ================================
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
)

echo.
echo Activating virtual environment...
call ".venv\Scripts\activate"

echo.
echo Upgrading pip...
py -m pip install --upgrade pip

echo.
echo Installing editable packages...
pip install -e .\api
pip install -e .\platform
pip install -e .\json-plugin

echo.
echo ================================
echo Installation complete!
echo ================================

echo.
echo ================================
echo Running test1_module...
echo ================================
python test1_module.py

echo.
echo ================================
echo Done!
echo ================================
pause