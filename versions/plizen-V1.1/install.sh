#!/bin/bash
# ============================================================
#  Pi Cockpit - One-Shot Install Script
#  Run this on your Raspberry Pi as the 'pi' user
#  Usage: bash install.sh
# ============================================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${YELLOW}[..] $1${NC}"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

echo ""
echo "  🥧  Pi Cockpit Installer"
echo "  ─────────────────────────"
echo ""

# 1. Check we're on a Pi
[[ "$(uname -m)" =~ ^arm|^aarch64 ]] || { echo "[WARN] Not on ARM — GPIO will be simulated."; }

# 2. System deps
info "Updating apt and installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv git --quiet
ok "System packages installed."

# 3. Create project directory
info "Setting up project directory..."
mkdir -p ~/pi-cockpit/{backend,frontend}
ok "Directory ~/pi-cockpit ready."

# 4. Copy files (assumes script is run from the repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/backend/app.py"         ~/pi-cockpit/backend/app.py
cp "$SCRIPT_DIR/backend/requirements.txt" ~/pi-cockpit/backend/requirements.txt
cp "$SCRIPT_DIR/frontend/index.html"    ~/pi-cockpit/frontend/index.html
ok "Files copied."

# 5. Python venv + deps
info "Creating Python virtual environment..."
python3 -m venv ~/pi-cockpit/venv
source ~/pi-cockpit/venv/bin/activate
pip install --upgrade pip --quiet
pip install -r ~/pi-cockpit/backend/requirements.txt --quiet
# RPi.GPIO might fail on non-Pi; that's fine
pip install RPi.GPIO 2>/dev/null || echo "[WARN] RPi.GPIO not installed (non-Pi system) — fan control simulated."
deactivate
ok "Python environment ready."

# 6. Sudoers for service control + reboot
info "Configuring sudoers..."
sudo cp "$SCRIPT_DIR/backend/cockpit-sudoers" /etc/sudoers.d/pi-cockpit
sudo chmod 0440 /etc/sudoers.d/pi-cockpit
ok "Sudoers configured."

# 7. Systemd service
info "Installing systemd service..."
sudo cp "$SCRIPT_DIR/backend/pi-cockpit.service" /etc/systemd/system/pi-cockpit.service
sudo sed -i "s|/home/pi|$HOME|g" /etc/systemd/system/pi-cockpit.service
sudo sed -i "s|User=pi|User=$(whoami)|g" /etc/systemd/system/pi-cockpit.service
sudo systemctl daemon-reload
sudo systemctl enable pi-cockpit.service
sudo systemctl restart pi-cockpit.service
ok "Systemd service enabled and started."

# 8. Fan GPIO pins reminder
echo ""
echo "  ─────────────────────────────────────────────"
echo "  🌀  Fan Wiring (4-pin PWM fans):"
echo ""
echo "    Fan 1 (CPU Fan):  PWM → GPIO 18  (Pin 12)"
echo "    Fan 2 (Case Fan): PWM → GPIO 12  (Pin 32)"
echo "    +5V  → Pin 4 or 6"
echo "    GND  → Pin 6 or 9"
echo ""
echo "  Edit ~/pi-cockpit/backend/app.py to change GPIO pins."
echo "  ─────────────────────────────────────────────"
echo ""

# 9. Done
IP=$(hostname -I | awk '{print $1}')
echo -e "${GREEN}"
echo "  ✅  Install complete!"
echo ""
echo "  Open your browser and go to:"
echo "       file://$HOME/pi-cockpit/frontend/index.html"
echo "  OR serve it with:"
echo "       python3 -m http.server 8080 --directory ~/pi-cockpit/frontend"
echo "  Then visit: http://${IP}:8080"
echo ""
echo "  Backend API running at: http://${IP}:5000"
echo -e "${NC}"
