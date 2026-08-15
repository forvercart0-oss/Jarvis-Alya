@echo off
chcp 65001 >nul
echo [JARVIS] Starting JARVIS 2.0...

cd /d "%~dp0"

if not exist ".venv" (
    echo [JARVIS] Virtual environment not found. Run install-windows.ps1 first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

if not exist "frontend\node_modules" (
    echo [JARVIS] Node modules not found. Run install-windows.ps1 first.
    pause
    exit /b 1
)

if not exist "frontend\dist" (
    echo [JARVIS] Frontend build not found. Run install-windows.ps1 first.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo [JARVIS] .env created
    )
)

echo [JARVIS] Starting backend...
start "JARVIS Backend" /B python main.py

timeout /t 5 /nobreak >nul

echo [JARVIS] Launching JARVIS desktop application...
cd frontend
npm run tauri:dev
cd ..
