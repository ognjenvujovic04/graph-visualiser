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
pip install -e .\simple-visualizer
pip install -e .\block-visualizer
pip install -e .\csv-plugin
pip install -e .\xml-plugin
pip install django
pip install flask

echo.
echo ================================
echo Installation complete!
echo.
echo Run test.bat to execute tests.
echo ================================
pause