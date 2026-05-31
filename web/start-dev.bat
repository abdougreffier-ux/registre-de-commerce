@echo off
chcp 65001 >nul
title Registre RC - Environnement de dev
color 0A

echo ============================================
echo   Registre du Commerce - Lancement Dev
echo ============================================
echo.

:: ── Chemins ─────────────────────────────────────────────
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend_django"
set "FRONTEND=%ROOT%frontend"

:: ── 1. Vérifier que le venv existe ──────────────────────
if not exist "%BACKEND%\venv\Scripts\activate.bat" (
    echo [ERREUR] Le venv n'existe pas dans backend_django\venv
    echo Créez-le avec : python -m venv venv
    pause
    exit /b 1
)

:: ── 2. Lancer le backend Django ─────────────────────────
echo [1/2] Lancement du backend Django (port 8000)...
start "Django Backend" cmd /k "cd /d "%BACKEND%" && venv\Scripts\activate.bat && python manage.py migrate --noinput 2>nul && echo. && echo === Backend pret : http://localhost:8000 === && echo. && python manage.py runserver 0.0.0.0:8000"

:: Petit delai pour laisser le backend demarrer
timeout /t 3 /nobreak >nul

:: ── 3. Lancer le frontend React ─────────────────────────
echo [2/2] Lancement du frontend React (port 3000)...
start "React Frontend" cmd /k "cd /d "%FRONTEND%" && echo === Frontend : http://localhost:3000 === && npm start"

echo.
echo ============================================
echo   Deux fenetres se sont ouvertes :
echo     - Backend Django  : http://localhost:8000
echo     - Frontend React  : http://localhost:3000
echo.
echo   Pour arreter : fermez les fenetres ou
echo   faites Ctrl+C dans chacune.
echo ============================================
echo.
pause
