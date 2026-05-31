@echo off
:: ============================================================
:: RCCM — Procédure de déploiement Windows
:: À exécuter depuis le dossier : web\backend_django
:: Usage : scripts\deploy.bat [--no-static]
:: ============================================================
setlocal EnableDelayedExpansion

set "BACKEND_DIR=%~dp0..\backend_django"
set "SKIP_STATIC=0"
if "%1"=="--no-static" set "SKIP_STATIC=1"

echo.
echo ===================================================
echo   RCCM -- Deploiement  ^|  %DATE% %TIME%
echo ===================================================
echo.

:: Vérifier qu'on est dans le bon dossier
if not exist "%BACKEND_DIR%\manage.py" (
    echo [ECHEC] manage.py introuvable dans %BACKEND_DIR%
    echo         Lancez ce script depuis web\
    exit /b 1
)

cd /d "%BACKEND_DIR%"

:: ── Étape 1 : Contrôle pré-déploiement ──────────────────────
echo [1/5] Controle pre-deploiement...
python manage.py check_deploy
if errorlevel 1 (
    echo.
    echo [AVERTISSEMENT] Des problemes ont ete detectes.
    echo Continuer quand meme ? (O/N)
    set /p CONT=
    if /i "!CONT!" neq "O" (
        echo Deploiement annule.
        exit /b 1
    )
)

:: ── Étape 2 : Appliquer les migrations ──────────────────────
echo.
echo [2/5] Application des migrations...
python manage.py migrate --no-input
if errorlevel 1 (
    echo [ECHEC] Les migrations ont echoue.
    exit /b 1
)
echo [OK] Migrations appliquees.

:: ── Étape 3 : Vérification finale du schéma ─────────────────
echo.
echo [3/5] Verification schema post-migration...
python manage.py check_deploy
if errorlevel 1 (
    echo [ECHEC] Le schema est toujours incoherent apres migration.
    exit /b 1
)
echo [OK] Schema coherent.

:: ── Étape 4 : Collectstatic (optionnel) ─────────────────────
if "%SKIP_STATIC%"=="0" (
    echo.
    echo [4/5] Collecte des fichiers statiques...
    python manage.py collectstatic --no-input --clear
    if errorlevel 1 (
        echo [AVERTISSEMENT] collectstatic a echoue - non bloquant.
    ) else (
        echo [OK] Fichiers statiques collectes.
    )
) else (
    echo [4/5] Collectstatic ignore (--no-static).
)

:: ── Étape 5 : Rapport final ──────────────────────────────────
echo.
echo ===================================================
echo   [OK] RCCM pret -- Demarrez le serveur :
echo        python manage.py runserver
echo ===================================================
echo.
exit /b 0
