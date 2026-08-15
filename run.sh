#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[JARVIS]${NC} $*"; }
ok()    { echo -e "${GREEN}[JARVIS]${NC} $*"; }
warn()  { echo -e "${YELLOW}[JARVIS]${NC} $*"; }
fail()  { echo -e "${RED}[JARVIS]${NC} $*"; }

# ---------------------------------------------------------------- checks
info "Starting JARVIS 2.0..."

check_cmd() {
  if command -v "$1" &>/dev/null; then
    ok "$2: OK ($(command -v "$1"))"
    return 0
  else
    fail "$2: MISSING"
    return 1
  fi
}

PYTHON_OK=0
NODE_OK=0
NPM_OK=0
CURL_OK=0
RUSTC_OK=0
CARGO_OK=0

check_cmd python3 "Python" || PYTHON_OK=1
check_cmd node "Node.js" || NODE_OK=1
check_cmd npm "npm" || NPM_OK=1
check_cmd curl "curl" || CURL_OK=1
check_cmd rustc "Rust" || RUSTC_OK=1
check_cmd cargo "Cargo" || CARGO_OK=1

if [[ $PYTHON_OK -ne 0 || $NODE_OK -ne 0 || $NPM_OK -ne 0 ]]; then
  fail "Missing dependencies. Run ./install.sh first."
  exit 1
fi

# ---------------------------------------------------------------- Python venv
info "Checking Python environment..."
if [[ ! -d ".venv" ]]; then
  warn "Virtual environment not found. Creating..."
  python3 -m venv .venv
  ok "Virtual environment created"
fi

source .venv/bin/activate

if [[ ! -f ".venv/.installed" ]] || [[ "requirements.txt" -nt ".venv/.installed" ]]; then
  warn "Installing Python dependencies..."
  PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install --timeout 120 --retries 10 --no-cache-dir -r requirements.txt
  touch .venv/.installed
  ok "Python dependencies installed"
else
  ok "Python dependencies: OK"
fi

# ---------------------------------------------------------------- Node dependencies
info "Checking Node dependencies..."
if [[ ! -d "frontend/node_modules" ]]; then
  warn "Node modules not found. Installing..."
  cd frontend
  npm install
  cd ..
  ok "Node dependencies installed"
else
  ok "Node dependencies: OK"
fi

# ---------------------------------------------------------------- Frontend build
info "Checking frontend build..."
if [[ ! -d "frontend/dist" ]] || [[ "frontend/src" -nt "frontend/dist" ]]; then
  warn "Building frontend..."
  cd frontend
  npm run build
  cd ..
  ok "Frontend built"
else
  ok "Frontend build: OK"
fi

# ---------------------------------------------------------------- Environment
info "Checking environment..."
if [[ ! -f ".env" ]]; then
  if [[ -f ".env.example" ]]; then
    warn ".env not found. Copying from .env.example..."
    cp .env.example .env
    ok ".env created from .env.example"
  else
    fail ".env and .env.example not found!"
    exit 1
  fi
else
  ok "Environment: OK"
fi

# ---------------------------------------------------------------- Backend
info "Starting backend..."
BACKEND_PID=$(lsof -ti tcp:8000 2>/dev/null || true)
if [[ -n "$BACKEND_PID" ]]; then
  ok "Backend already running (PID $BACKEND_PID)"
else
  nohup python3 main.py > logs/jarvis-backend.log 2>&1 &
  BACKEND_PID=$!
  ok "Backend started (PID $BACKEND_PID)"
fi

# Wait for backend
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

# ---------------------------------------------------------------- Desktop
info "Checking desktop environment..."

# Check if Tauri is available
TAURI_AVAILABLE=0
if [[ -f "frontend/node_modules/.bin/tauri" ]] || command -v tauri &>/dev/null; then
  TAURI_AVAILABLE=1
  ok "Tauri: AVAILABLE"
else
  warn "Tauri: NOT AVAILABLE (install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh)"
  warn "Then run: cd frontend && npm install && cd .. && ./run.sh"
fi

if [[ $TAURI_AVAILABLE -eq 1 ]]; then
  info "Launching JARVIS desktop application..."
  echo ""
  echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║   JARVIS 2.0  —  Desktop Mode       ║${NC}"
  echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
  echo ""

  # Launch Tauri from frontend directory where scripts are defined
  cd frontend
  npm run tauri:dev
  cd ..
else
  fail "Cannot launch desktop mode without Tauri."
  fail "Install Rust and run: cd frontend && npm install"
  exit 1
fi
