@echo off
setlocal
echo "Installation du Service Windows AKA-NODE"
echo "----------------------------------------"

set TASK_NAME=AKA-Node-Daemon
set SCRIPT_PATH=%~dp0client_daemon.py
set PYTHON_EXE=pythonw.exe

:: Create a VBScript to run pythonw silently in background
set VBS_RUNNER=%~dp0run_daemon_silent.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_RUNNER%"
echo WshShell.Run "%PYTHON_EXE% ""%SCRIPT_PATH%""", 0, False >> "%VBS_RUNNER%"

echo Création de la tache planifiée...
schtasks /create /tn "%TASK_NAME%" /tr "wscript.exe \"%VBS_RUNNER%\"" /sc onlogon /ru "%USERNAME%" /rl highest /f

if %ERRORLEVEL% EQU 0 (
    echo [SUCCES] La tache planifiée a été créée. Le Daemon se lancera silencieusement à chaque connexion de l'utilisateur.
    echo Pour lancer le Daemon immédiatement, veuillez exécuter : schtasks /run /tn "%TASK_NAME%"
) else (
    echo [ERREUR] Impossible de créer la tache. Assurez-vous d'Exécuter en tant qu'Administrateur.
)

pause
