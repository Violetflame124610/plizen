#!/bin/bash
# ============================================================
#  Plizen Installer — v1.1 Passwordless Edition
#  The open source Pi management dashboard
#  Made by Dhruva — github.com/Violetflame124610/plizen
#
#  Usage:
#  curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.1/install.sh | bash
# ============================================================

set -e
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
echo -e "  Made by Dhruva · Version 1.1 (Passwordless Edition)"
echo -e "  ─────────────────────────────────────────────"
echo ""
echo -e "  ${YELLOW}[!]${NC} Warning: Terminal has no authentication in this version."
echo -e "      Only use on a private trusted network."
echo -e "      For the secure version use v1.2."
echo ""

ok()   { echo -e "  ${GREEN}[✓]${NC} $1"; }
info() { echo -e "  ${YELLOW}[·]${NC} $1"; }
err()  { echo -e "  ${RED}[✗]${NC} $1"; exit 1; }

[[ "$(uname -m)" =~ ^arm|^aarch64 ]] || echo -e "  ${YELLOW}[!]${NC} Not ARM — fan control will be unavailable."

# 1. System packages
info "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip git --quiet
ok "System packages ready."

# 2. Create directory
info "Setting up /opt/plizen..."
sudo mkdir -p /opt/plizen
sudo chown $(whoami):$(whoami) /opt/plizen

# 3. Download files
info "Downloading Plizen v1.1 files..."
BASE="https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.1"
curl -sSL "$BASE/app.py"     -o /opt/plizen/app.py
curl -sSL "$BASE/index.html" -o /opt/plizen/index.html
ok "Files downloaded."

# 4. Fix backend URL in index.html
IP=$(hostname -I | awk '{print $1}')
info "Setting backend URL to http://${IP}:5000 ..."
sed -i "s|const BACKEND = \".*\"|const BACKEND = \"http://${IP}:5000\"|" /opt/plizen/index.html
ok "Backend URL set."

# 5. Install Python deps
info "Installing Python dependencies..."
pip install flask flask-cors flask-socketio --break-system-packages --quiet
ok "Python dependencies installed."

# 6. udev rule for fan control
info "Setting up fan control permissions..."
echo 'SUBSYSTEM=="hwmon", ATTR{name}=="pwmfan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"' | sudo tee /etc/udev/rules.d/99-plizen-fan.rules > /dev/null
echo 'SUBSYSTEM=="hwmon", ATTR{name}=="rpi-pwm-fan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"' | sudo tee -a /etc/udev/rules.d/99-plizen-fan.rules > /dev/null
sudo udevadm control --reload-rules && sudo udevadm trigger
ok "Fan control permissions set."

# 7. Systemd backend service
info "Creating plizen backend service..."
sudo tee /etc/systemd/system/plizen.service > /dev/null << SVCEOF
[Unit]
Description=Plizen Backend v1.1
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=/opt/plizen
ExecStart=/usr/bin/python3 /opt/plizen/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

# 8. Systemd frontend service
info "Creating plizen web service..."
sudo tee /etc/systemd/system/plizen-web.service > /dev/null << SVCEOF
[Unit]
Description=Plizen Web UI v1.1
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

# 9. Enable and start
info "Enabling and starting Plizen services..."
sudo systemctl daemon-reload
sudo systemctl enable plizen plizen-web
sudo systemctl restart plizen plizen-web
ok "Services started."

# Done
echo ""
echo -e "  ${GREEN}${BOLD}✅  Plizen v1.1 installed successfully!${NC}"
echo ""
echo -e "  ${BOLD}Open your browser and go to:${NC}"
echo -e "  ${BLUE}  http://${IP}:9090${NC}"
echo ""
echo -e "  Manage services with:"
echo -e "    sudo systemctl status plizen"
echo -e "    sudo systemctl restart plizen"
echo -e "    sudo systemctl stop plizen"
echo ""
echo -e "  ${YELLOW}Upgrade to v1.2 (with secure terminal):${NC}"
echo -e "    curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/install.sh | bash"
echo ""
echo -e "  ─────────────────────────────────────────────"
echo -e "  Plizen v1.1 · Made by Dhruva"
echo ""
