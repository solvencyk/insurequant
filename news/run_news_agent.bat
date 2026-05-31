@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1

echo [뉴스 스크래핑 Agent] Streamlit 실행 중...
echo 폴더: %CD%
echo.

python -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo 실행 실패. scrapping 폴더에서 pip install -r requirements.txt 를 먼저 실행했는지 확인하세요.
    pause
)
