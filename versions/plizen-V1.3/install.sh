#!/bin/bash
# Plizen v1.3 Installer
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
clear
echo -e "${BLUE}${BOLD}"
echo "  ██████╗ ██╗     ██╗███████╗███████╗███╗   ██╗"
echo "  ██╔══██╗██║     ██║╚══███╔╝██╔════╝████╗  ██║"
echo "  ██████╔╝██║     ██║  ███╔╝ █████╗  ██╔██╗ ██║"
echo "  ██╔═══╝ ██║     ██║ ███╔╝  ██╔══╝  ██║╚██╗██║"
echo "  ██║     ███████╗██║███████╗███████╗██║ ╚████║"
echo "  ╚═╝     ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝"
echo -e "${NC}"
echo -e "  ${BOLD}The open source Pi management dashboard${NC}"
echo -e "  Made by Dhruva · Version 1.3"
echo -e "  ─────────────────────────────────────────────"
echo ""
set -e
ok()   { echo -e "  ${GREEN}[✓]${NC} $1"; }
info() { echo -e "  ${YELLOW}[·]${NC} $1"; }
err()  { echo -e "  ${RED}[✗]${NC} $1"; exit 1; }

[[ "$(uname -m)" =~ ^arm|^aarch64 ]] || echo -e "  ${YELLOW}[!]${NC} Not ARM — fan control unavailable."

info "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip curl libpam-python --quiet
ok "System packages ready."

info "Setting up /opt/plizen..."
sudo mkdir -p /opt/plizen
sudo chown $(whoami):$(whoami) /opt/plizen

info "Downloading Plizen v1.3 files..."
BASE="https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.3"
curl -sSL "$BASE/app.py"     -o /opt/plizen/app.py
curl -sSL "$BASE/index.html" -o /opt/plizen/index.html
if ! grep -q "Plizen v1.3" /opt/plizen/app.py; then err "Download failed — check GitHub repo."; fi
ok "Files downloaded."

IP=$(hostname -I | awk '{print $1}')

info "Installing Python dependencies..."
pip install flask flask-cors flask-socketio python-pam --break-system-packages --quiet
ok "Python dependencies installed."

info "Setting up fan control permissions..."
echo 'SUBSYSTEM=="hwmon", ATTR{name}=="pwmfan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"' | sudo tee /etc/udev/rules.d/99-plizen-fan.rules > /dev/null
echo 'SUBSYSTEM=="hwmon", ATTR{name}=="rpi-pwm-fan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"' | sudo tee -a /etc/udev/rules.d/99-plizen-fan.rules > /dev/null
sudo udevadm control --reload-rules && sudo udevadm trigger
ok "Fan permissions set."

info "Adding $(whoami) to shadow group for PAM auth..."
sudo usermod -a -G shadow $(whoami) || true
ok "Shadow group configured."

info "Creating systemd services..."
sudo tee /etc/systemd/system/plizen.service > /dev/null << SVCEOF
[Unit]
Description=Plizen v1.3 Backend
After=network.target
[Service]
User=root
WorkingDirectory=/opt/plizen
ExecStart=/usr/bin/python3 /opt/plizen/app.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVCEOF

sudo tee /etc/systemd/system/plizen-web.service > /dev/null << SVCEOF
[Unit]
Description=Plizen v1.3 Web UI
After=network.target
[Service]
User=$(whoami)
WorkingDirectory=/opt/plizen
ExecStart=/usr/bin/python3 -m http.server 9090 --directory /opt/plizen
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVCEOF

info "Starting Plizen services..."
sudo systemctl daemon-reload
sudo systemctl enable plizen plizen-web
sudo systemctl restart plizen plizen-web
ok "Services started."

echo ""
echo -e "  ${GREEN}${BOLD}✅  Plizen v1.3 installed!${NC}"
echo ""
echo -e "  ${BOLD}Open your browser:${NC}"
echo -e "  ${BLUE}  http://${IP}:9090${NC}"
echo ""
echo -e "  Sign in with your Raspberry Pi username and password."
echo ""
echo -e "  Manage:"
echo -e "    sudo systemctl status plizen"
echo -e "    sudo systemctl restart plizen"
echo -e "    sudo systemctl stop plizen"
echo ""
echo -e "  ─────────────────────────────────────────────"
echo -e "  Plizen v1.3 · Made by Dhruva"
echo ""
