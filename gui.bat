@echo off
cd /d "%~dp0"
echo ========================================
echo   vpbar 视频进度条生成器 - GUI 启动中...
echo ========================================
echo.
streamlit run vpbar/app.py
if errorlevel 1 (
    echo.
    echo 启动失败。请先运行: pip install -e .
    pause
)
