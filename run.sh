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

info "Starting JARVIS 2.0..."

# ---------------------------------------------------------------- checks
check_cmd() {
  if command -v "$1" &>/dev/null; then
    ok "$2: OK"
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

# ---------------------------------------------------------------- verify installation
info "Verifying installation..."
if [[ ! -d ".venv" ]]; then
  fail "Python virtual environment not found. Run ./install.sh first."
  exit 1
fi
if [[ ! -d "frontend/node_modules" ]]; then
  fail "Node modules not found. Run ./install.sh first."
  exit 1
fi
warn "Building frontend..."
cd frontend
npm run build
cd ..
ok "Frontend built"
if [[ ! -f ".env" ]]; then
  warn ".env not found. Copying from .env.example..."
  cp .env.example .env
  ok ".env created"
fi

# ---------------------------------------------------------------- backend
info "Starting backend..."
source .venv/bin/activate
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

# ---------------------------------------------------------------- desktop
info "Launching JARVIS desktop application..."
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   JARVIS 2.0  —  Desktop Mode       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

if [[ -f "frontend/node_modules/.bin/tauri" ]] || command -v tauri &>/dev/null; then
  if [[ -f "frontend/node_modules/.bin/tauri" ]]; then
    "$SCRIPT_DIR/frontend/node_modules/.bin/tauri" dev
  else
    tauri dev
  fi
else
  fail "Tauri not available. Run ./install.sh to set up Rust."
  exit 1
fi
