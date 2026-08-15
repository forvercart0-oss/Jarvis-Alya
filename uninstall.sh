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

info "Uninstalling JARVIS 2.0..."

# Remove desktop launcher
if [[ -f "$HOME/.local/share/applications/jarvis.desktop" ]]; then
  rm "$HOME/.local/share/applications/jarvis.desktop"
  ok "Removed desktop launcher"
fi

# Remove icons
if [[ -f "$HOME/.local/share/icons/jarvis.png" ]]; then
  rm "$HOME/.local/share/icons/jarvis.png"
fi
if [[ -f "$HOME/.local/share/icons/jarvis-512.png" ]]; then
  rm "$HOME/.local/share/icons/jarvis-512.png"
fi
ok "Removed application icons"

# Update desktop database
if command -v update-desktop-database &>/dev/null; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

# Ask about data
echo ""
warn "This will NOT delete your data, memories, or configuration."
warn "If you want to remove everything, delete this directory manually:"
echo "  $SCRIPT_DIR"
echo ""

read -p "Remove Python virtual environment (.venv)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -rf .venv
  ok "Removed .venv"
fi

read -p "Remove Node modules (frontend/node_modules)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -rf frontend/node_modules
  ok "Removed node_modules"
fi

read -p "Remove frontend build (frontend/dist)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -rf frontend/dist
  ok "Removed frontend/dist"
fi

read -p "Remove data directory (data/ with database and projects)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -rf data
  ok "Removed data/"
fi

read -p "Remove .env configuration? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  rm -f .env
  ok "Removed .env"
fi

echo ""
ok "JARVIS 2.0 uninstalled."
