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

# ---------------------------------------------------------------- OS detection
detect_os() {
  if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "$ID"
  else
    echo "unknown"
  fi
}

OS_ID=$(detect_os)
info "Detected OS: $OS_ID"

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
  read -p "Install missing packages now? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    fail "Cannot continue without required packages."
    exit 1
  fi
  if command -v pacman &>/dev/null; then
    sudo pacman -S --needed python3 python-pip python-virtualenv nodejs npm
  else
    fail "Automatic install not supported on this distro. Please install: ${missing[*]}"
    exit 1
  fi
fi

# ---------------------------------------------------------------- Tauri deps
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
  missing_tauri=()
  for pkg in "${TAURI_PKGS[@]}"; do
    if ! pacman -Q "$pkg" &>/dev/null; then
      missing_tauri+=("$pkg")
    fi
  done
  if [[ ${#missing_tauri[@]} -gt 0 ]]; then
    warn "Missing Tauri dependencies: ${missing_tauri[*]}"
    read -p "Install missing Tauri packages now? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      warn "Skipping Tauri dependencies. Desktop app may not build."
    else
      sudo pacman -S --needed "${missing_tauri[@]}"
      ok "Tauri dependencies installed"
    fi
  else
    ok "Tauri dependencies: OK"
  fi
else
  warn "Not on Arch Linux. Ensure Tauri build dependencies are installed."
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

if ! pip install $PIP_OPTS -r requirements.txt; then
  fail "pip install failed. See troubleshooting in README."
  exit 1
fi
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
    warn "Edit .env to add your API keys (GROQ_API_KEY, etc.)"
  fi
fi

# ---------------------------------------------------------------- Data dirs
mkdir -p data/generated/images data/generated/videos logs
ok "Data directories prepared"

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

cp assets/app-icon.png "$HOME/.local/share/icons/jarvis.png" 2>/dev/null || true
cp assets/app-icon-512.png "$HOME/.local/share/icons/jarvis-512.png" 2>/dev/null || true

if command -v update-desktop-database &>/dev/null; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

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
info "Run: ./run.sh"
info "Or from your application menu: JARVIS 2.0"
info "Edit .env to configure your AI providers"
