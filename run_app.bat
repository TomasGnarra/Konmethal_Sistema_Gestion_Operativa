@echo off
echo ========================================================
echo   Iniciando Konmethal - Sistema de Gestion Operativa
echo ========================================================
echo.

echo [1/2] Iniciando Backend FastAPI en segundo plano (Puerto 8000)...
start "Konmethal Backend (API)" cmd /c "py -m uvicorn api.main:app --reload --port 8000"

echo [2/2] Iniciando Frontend Streamlit...
echo Se abrira tu navegador de internet en breve.
py -m streamlit run app/main.py

echo.
echo Presiona cualquier tecla para cerrar todo.
pause >nul
