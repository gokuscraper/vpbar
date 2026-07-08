@echo off
cd /d "%~dp0"
echo ========================================
echo   vpbar GUI - Launching...
echo ========================================
echo.
streamlit run app.py
if errorlevel 1 (
    echo.
    echo Failed. Run: pip install -e .
    pause
)