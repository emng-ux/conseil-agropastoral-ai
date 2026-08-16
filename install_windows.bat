@echo off
REM ============================================================
REM  Conseil Agropastoral IA — Installation Windows (1 clic)
REM  Ce script automatise tout ce qui a ete fait manuellement :
REM  verification de Python/Git, clonage du depot, creation de
REM  l'environnement virtuel, installation des dependances, et
REM  lancement de l'application.
REM ============================================================

setlocal enabledelayedexpansion
title Conseil Agropastoral IA - Installation

echo.
echo ============================================
echo   Conseil Agropastoral IA - Installation
echo ============================================
echo.

REM --- Verification de Python ---
where py >nul 2>nul
if %errorlevel% neq 0 (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERREUR] Python n'est pas installe sur cet ordinateur.
        echo Va sur https://www.python.org/downloads/ et installe Python
        echo en cochant bien la case "Add Python to PATH" pendant l'installation.
        echo Relance ensuite ce script.
        pause
        exit /b 1
    )
    set PYCMD=python
) else (
    set PYCMD=py
)
echo [OK] Python detecte.

REM --- Verification de Git ---
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] Git n'est pas installe sur cet ordinateur.
    echo Va sur https://git-scm.com/download/win et installe Git
    echo ^(options par defaut^), puis relance ce script.
    pause
    exit /b 1
)
echo [OK] Git detecte.
echo.

REM --- Dossier d'installation (Documents\conseil-agropastoral-ai) ---
set INSTALL_DIR=%USERPROFILE%\Documents\conseil-agropastoral-ai

if exist "%INSTALL_DIR%" (
    echo Le dossier existe deja, mise a jour du code...
    cd /d "%INSTALL_DIR%"
    git pull
) else (
    echo Telechargement du projet...
    cd /d "%USERPROFILE%\Documents"
    git clone https://github.com/emng-ux/conseil-agropastoral-ai.git
    cd /d "%INSTALL_DIR%"
)
echo.

REM --- Environnement virtuel ---
if not exist "venv" (
    echo Creation de l'environnement Python...
    %PYCMD% -m venv venv
)

echo Activation de l'environnement...
call venv\Scripts\activate.bat

echo Installation des dependances (peut prendre 1 a 2 minutes)...
pip install -q -r requirements.txt

echo.
echo ============================================
echo   Installation terminee ! Lancement...
echo ============================================
echo.
echo Un onglet de navigateur va s'ouvrir automatiquement.
echo Pour relancer l'agent plus tard, utilise plutot
echo le fichier "lancer_agent.bat" (plus rapide).
echo.

streamlit run app.py

pause
