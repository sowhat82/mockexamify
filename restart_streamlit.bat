@echo off
echo Stopping Streamlit...
taskkill //F //IM streamlit.exe 2>nul

echo Clearing cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist .streamlit\cache rmdir /s /q .streamlit\cache

echo.
echo Starting Streamlit...
echo.
streamlit run streamlit_app.py
