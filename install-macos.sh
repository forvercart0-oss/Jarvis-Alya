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

info "Installing JARVIS 2.0 for macOS..."

# ---------------------------------------------------------------- OS detection
if [[ "$(uname)" != "Darwin" ]]; then
    fail "This script is for macOS only."
    exit 1
fi

# ---------------------------------------------------------------- Package manager detection
PKG_MGR="none"
if command -v brew &>/dev/null; then
    PKG_MGR="brew"
elif command -v port &>/dev/null; then
    PKG_MGR="macports"
fi

info "Package manager: $PKG_MGR"

# ---------------------------------------------------------------- System deps
info "Checking system dependencies..."

missing=()
for cmd in python3 pip node npm; do
    if ! command -v "$cmd" &>/dev/null; then
        missing+=("$cmd")
    fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
    warn "Missing system packages: ${missing[*]}"
    read -p "Install missing packages now? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]; then
        fail "Cannot continue without required packages."
        exit 1
    fi
    if [[ "$PKG_MGR" == "brew" ]]; then
        brew install python node git
    elif [[ "$PKG_MGR" == "macports" ]]; then
        sudo port install python311 nodejs git
    else
        fail "No supported package manager. Install: ${missing[*]}"
        exit 1
    fi
fi

# ---------------------------------------------------------------- Xcode Command Line Tools
if ! xcode-select -p &>/dev/null; then
    warn "Xcode Command Line Tools not found."
    read -p "Install Xcode Command Line Tools now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xcode-select --install
        ok "Xcode Command Line Tools installer launched. Follow the prompts."
    else
        warn "Skipping. Tauri build may fail."
    fi
fi

# ---------------------------------------------------------------- Rust
info "Checking Rust..."
if ! command -v cargo &>/dev/null; then
    warn "Rust not found. Installing via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal
    source "$HOME/.cargo/env"
    ok "Rust installed"
else
    ok "Rust: OK"
fi

# ---------------------------------------------------------------- Python venv
info "Setting up Python environment..."
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    ok "Virtual environment created"
fi

source .venv/bin/activate

PIP_OPTS="--timeout 60 --retries 5"
if [[ "${JARVIS_PIP_MIRROR:-}" != "" ]]; then
    PIP_OPTS="$PIP_OPTS -i ${JARVIS_PIP_MIRROR}"
fi

pip install $PIP_OPTS -r requirements.txt
ok "Python dependencies installed"

# ---------------------------------------------------------------- Node deps
info "Installing Node dependencies..."
cd frontend
npm install --no-audit --no-fund
cd ..
ok "Node dependencies installed"

# ---------------------------------------------------------------- Build frontend
info "Building frontend..."
cd frontend
npm run build
cd ..
ok "Frontend built"

# ---------------------------------------------------------------- Environment
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        ok ".env created from .env.example"
        warn "Edit .env to add your API keys"
    fi
fi

# ---------------------------------------------------------------- Data dirs
mkdir -p data/generated/images data/generated/videos logs
ok "Data directories prepared"

# ---------------------------------------------------------------- Desktop launcher
info "Creating desktop launcher..."
mkdir -p "$HOME/Applications"

SCRIPT_ABS="$(cd "$SCRIPT_DIR" && pwd)/run-macos.sh"

cat > "$HOME/Applications/JARVIS 2.0.command" << LAUNCHER
#!/bin/bash
cd "$SCRIPT_DIR"
./run-macos.sh
LAUNCHER

chmod +x "$HOME/Applications/JARVIS 2.0.command"
ok "Desktop launcher created"

# ---------------------------------------------------------------- Tauri CLI
info "Setting up Tauri..."
cd frontend
npm install @tauri-apps/cli 2>/dev/null || true
cd ..

# ---------------------------------------------------------------- Done
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   JARVIS INSTALLATION COMPLETE       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
info "Run: ./run-macos.sh"
info "Or from Applications folder: JARVIS 2.0"
