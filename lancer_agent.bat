@echo off
REM ============================================================
REM  Conseil Agropastoral IA — Lancement rapide (apres installation)
REM  A utiliser une fois install_windows.bat execute une premiere fois.
REM ============================================================

title Conseil Agropastoral IA
cd /d "%~dp0"

if not exist "venv" (
    echo [ERREUR] L'environnement n'est pas installe.
    echo Execute d'abord install_windows.bat.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Verification des mises a jour...
git pull

echo Lancement de l'agent...
streamlit run app.py

pause
