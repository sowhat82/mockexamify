@echo off
echo Forcing complete reload...
echo.

REM Kill all Python and Streamlit processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1

REM Delete ALL cache
echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1

echo Clearing Streamlit cache...
if exist .streamlit\cache rd /s /q .streamlit\cache

REM Clear browser cache instruction
echo.
echo ========================================
echo IMPORTANT: Clear your browser cache!
echo ========================================
echo.
echo In your browser:
echo 1. Press Ctrl+Shift+Delete
echo 2. Select "Cached images and files"
echo 3. Click Clear Data
echo.
echo OR just do a hard refresh:
echo - Press Ctrl+F5 (Windows)
echo - Or Ctrl+Shift+R
echo.
pause

REM Start fresh
echo Starting Streamlit...
streamlit run streamlit_app.py --server.headless=true --server.port=8501 --browser.gatherUsageStats=false
