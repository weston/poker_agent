@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing poker-agent...
pip install -e .

echo.
echo Installation complete!
echo.
echo To activate the environment, run:
echo     venv\Scripts\activate
echo.
echo To start the agent, run:
echo     poker-agent
echo.
echo Don't forget to create your .env file from .env.example
