@echo off
REM Double-cliquez sur ce fichier pour installer l'agent Conseil Agropastoral IA.
REM Il appelle install.ps1 en autorisant son execution pour cette seule fois
REM (sans changer les reglages de securite globaux de Windows).

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
