#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[JARVIS]${NC} $*"; }
ok()    { echo -e "${GREEN}[JARVIS]${NC} $*"; }
warn()  { echo -e "${YELLOW}[JARVIS]${NC} $*"; }
fail()  { echo -e "${RED}[JARVIS]${NC} $*"; }

info "Starting JARVIS 2.0 on macOS..."

# Verify installation
if [[ ! -d ".venv" ]]; then
    fail "Virtual environment not found. Run ./install-macos.sh first."
    exit 1
fi

if [[ ! -d "frontend/node_modules" ]]; then
    fail "Node modules not found. Run ./install-macos.sh first."
    exit 1
fi

if [[ ! -d "frontend/dist" ]]; then
    warn "Frontend build not found. Building..."
    cd frontend
    npm run build
    cd ..
    ok "Frontend built"
fi

if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        ok ".env created"
    fi
fi

# Activate venv
source .venv/bin/activate

# Start backend
info "Starting backend..."
BACKEND_PID=$(lsof -ti tcp:8000 2>/dev/null || true)
if [[ -n "$BACKEND_PID" ]]; then
    ok "Backend already running (PID $BACKEND_PID)"
else
    nohup python3 main.py > logs/jarvis-backend.log 2>&1 &
    BACKEND_PID=$!
    ok "Backend started (PID $BACKEND_PID)"
fi

for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
        ok "Backend: ONLINE"
        break
    fi
    if [[ $i -eq 30 ]]; then
        fail "Backend failed to start"
        exit 1
    fi
    sleep 1
done

# Launch Tauri desktop app
info "Launching JARVIS desktop application..."
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   JARVIS 2.0  —  Desktop Mode       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

APP_BUNDLE="$SCRIPT_DIR/src-tauri/target/release/bundle/macos/JARVIS 2.0.app"
RELEASE_BIN="$SCRIPT_DIR/src-tauri/target/release/jarvis"

if [[ -d "$APP_BUNDLE" ]]; then
    ok "Launching release application..."
    # Record where the backend lives so the app can find it from anywhere.
    echo "$SCRIPT_DIR" > "$APP_BUNDLE/Contents/Resources/backend_path"
    open "$APP_BUNDLE"
    exit 0
fi

if [[ -x "$RELEASE_BIN" ]]; then
    ok "Launching release build..."
    exec "$RELEASE_BIN"
fi

warn "Release build not found. Falling back to development mode..."
warn "Run ./install-macos.sh (or npm run tauri:build) once to build the application."
cd frontend
npm run tauri:dev
