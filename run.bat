@echo off
echo Starting Personal Notes App...

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Please wait, creating it now...
    python -m venv venv
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

:: Run Streamlit directly using the virtual environment's Python
venv\Scripts\python.exe -m streamlit run app.py
pause
