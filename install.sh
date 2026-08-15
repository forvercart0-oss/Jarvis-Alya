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

info "Installing JARVIS 2.0..."

# ---------------------------------------------------------------- system deps
info "Checking system dependencies..."

missing=()
for cmd in python3 pip python3-venv node npm; do
  if ! command -v "$cmd" &>/dev/null; then
    missing+=("$cmd")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  warn "Missing system packages: ${missing[*]}"
  warn "Install them with:"
  echo "  sudo pacman -S --needed python python-pip python-virtualenv nodejs npm"
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# ---------------------------------------------------------------- Tauri system deps
info "Checking Tauri desktop dependencies..."
if command -v pacman &>/dev/null; then
  TAURI_PKGS=(
    webkit2gtk-4.1
    libappindicator-gtk3
    librsvg
    libxdo
    openssl
    base-devel
    cmake
    patchelf
    pkg-config
  )
  for pkg in "${TAURI_PKGS[@]}"; do
    if ! pacman -Q "$pkg" &>/dev/null; then
      warn "Missing Tauri dependency: $pkg"
      warn "Install with: sudo pacman -S --needed ${TAURI_PKGS[*]}"
      read -p "Continue anyway? (y/N) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
      fi
      break
    fi
  done
else
  warn "Not on Arch Linux. Ensure Tauri build dependencies are installed."
fi

# ---------------------------------------------------------------- Rust (for Tauri)
info "Checking Rust (required for Tauri desktop)..."
if ! command -v cargo &>/dev/null; then
  warn "Rust not found. Installing via rustup..."
  if ! command -v curl &>/dev/null; then
    fail "curl is required to install Rust. Install it first: sudo pacman -S curl"
    exit 1
  fi
  for i in 1 2 3; do
    echo "  Attempt $i/3..."
    if curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal; then
      break
    fi
    warn "Rust install attempt $i failed. Retrying in 5s..."
    sleep 5
  done
  if [[ -f "$HOME/.cargo/env" ]]; then
    source "$HOME/.cargo/env"
    ok "Rust installed"
  else
    fail "Rust installation failed after 3 attempts"
    warn "Tauri desktop will be unavailable. You can still use JARVIS in browser mode."
  fi
else
  ok "Rust: OK"
fi

# ---------------------------------------------------------------- PipeWire
info "Checking PipeWire..."
if ! command -v pactl &>/dev/null; then
  warn "PipeWire not found. Install with: sudo pacman -S pipewire pipewire-pulse wireplumber"
else
  ok "PipeWire: OK"
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

if ! pip install $PIP_OPTS -r requirements.txt; then
  fail "pip install failed. Retry options:"
  echo "  1. Retry:"
  echo "     source .venv/bin/activate && pip install --timeout 60 --retries 5 -r requirements.txt"
  echo "  2. Use a faster mirror (example for Iran):"
  echo "     JARVIS_PIP_MIRROR=https://pypi.daria.au/dev/ ./install.sh"
  echo "  3. Or set a global pip mirror:"
  echo "     pip config set global.index-url https://pypi.daria.au/dev/"
  echo ""
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
else
  ok "Python dependencies installed"
fi

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
    warn "Edit .env to add your API keys (GROQ_API_KEY, etc.)"
  fi
fi

# ---------------------------------------------------------------- Desktop launcher
info "Creating desktop launcher..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons"

SCRIPT_ABS="$(cd "$SCRIPT_DIR" && pwd)/run.sh"

cat > "$HOME/.local/share/applications/jarvis.desktop" << DESKTOP
[Desktop Entry]
Name=JARVIS 2.0
Comment=Advanced Personal AI Assistant
Exec=$SCRIPT_ABS
Icon=jarvis
Terminal=false
Type=Application
Categories=Utility;AI;Development;
StartupWMClass=jarvis
DESKTOP

# Copy icons
cp assets/app-icon.png "$HOME/.local/share/icons/jarvis.png"
cp assets/app-icon-512.png "$HOME/.local/share/icons/jarvis-512.png"

# Update desktop database
if command -v update-desktop-database &>/dev/null; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

ok "Desktop launcher created at ~/.local/share/applications/jarvis.desktop"

# ---------------------------------------------------------------- Tauri dev setup
info "Setting up Tauri..."
cd frontend
npm install @tauri-apps/cli 2>/dev/null || true
cd ..

# ---------------------------------------------------------------- Done
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   JARVIS 2.0  —  Installation Done   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
info "Launch with: ./run.sh"
info "Or from your application menu: JARVIS 2.0"
info "Edit .env to configure your AI providers"
