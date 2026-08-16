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
if exist "src-tauri\target\release\jarvis.exe" (
    echo [JARVIS] Launching release build...
    start "" "src-tauri\target\release\jarvis.exe"
    exit /b 0
)

echo [JARVIS] Release build not found, falling back to development mode...
echo [JARVIS] Run install-windows.ps1 to build the application.
cd frontend
npm run tauri:dev
cd ..
