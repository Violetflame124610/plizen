#!/bin/bash
# ============================================================
#  ____  _    _  ____  ____  ____  _  _
# (  _ \( )  ( )(_  _)(_   )( ___)( \( )
#  ) __/ )()( _)  )(   / /_  )__)  )  (
# (__)  \____/(__)(__)(____)(____)(_)\_)
#
#  Plizen — The open source Pi management dashboard
#  Version 1.2 | By Dhruva
#  https://github.com/Violetflame124610/plizen
#
#  Usage:
#    curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/install.sh | bash
# ============================================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

PLIZEN_VERSION="1.2"
PLIZEN_DIR="$HOME/plizen"
PLIZEN_USER="$(whoami)"
GITHUB_RAW="https://raw.githubusercontent.com/Violetflame124610/plizen/main"

ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${CYAN}[→]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
line() { echo -e "${CYAN}──────────────────────────────────────${NC}"; }

clear
echo -e "${CYAN}${BOLD}"
cat << 'EOF'
 ____  _    _  ____  ____  ____  _  _
(  _ \( )  ( )(_  _)(_   )( ___)( \( )
 ) __/ )()( _)  )(   / /_  )__)  )  (
(__)  \____/(__)(__)(____)(____)(_)\_)
EOF
echo -e "${NC}"
echo -e "  ${BOLD}The open source Pi management dashboard${NC}"
echo -e "  Version ${CYAN}${PLIZEN_VERSION}${NC} — by Dhruva"
echo -e "  https://github.com/Violetflame124610/plizen"
line

# ── Step 1: Check platform ─────────────────────────────────────────────────
info "Checking platform..."
[[ "$(uname -m)" =~ ^arm|^aarch64 ]] && ok "Raspberry Pi detected." || warn "Not ARM — GPIO/fan features may not work."

# ── Step 2: Apt dependencies ───────────────────────────────────────────────
info "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv --quiet
ok "System packages ready."

# ── Step 3: Create directory ───────────────────────────────────────────────
info "Setting up Plizen directory at $PLIZEN_DIR..."
mkdir -p "$PLIZEN_DIR"
ok "Directory created."

# ── Step 4: Download files ─────────────────────────────────────────────────
info "Downloading Plizen files from GitHub..."
curl -sSL "$GITHUB_RAW/backend/app.py"        -o "$PLIZEN_DIR/app.py"
curl -sSL "$GITHUB_RAW/frontend/index.html"   -o "$PLIZEN_DIR/index.html"
ok "Files downloaded."

# ── Step 5: Python venv ────────────────────────────────────────────────────
info "Creating Python virtual environment..."
python3 -m venv "$PLIZEN_DIR/venv"
source "$PLIZEN_DIR/venv/bin/activate"
pip install --upgrade pip --quiet
pip install flask flask-cors flask-socketio --quiet
deactivate
ok "Python environment ready."

# ── Step 6: Set terminal password ──────────────────────────────────────────
line
echo -e "${BOLD}  Set your Plizen terminal password${NC}"
echo -e "  This is used to unlock the read-only terminal in the dashboard."
echo ""
read -s -p "  Enter terminal password: " TERM_PASS
echo ""
read -s -p "  Confirm terminal password: " TERM_PASS2
echo ""
[[ "$TERM_PASS" == "$TERM_PASS2" ]] || err "Passwords do not match."
sed -i "s|TERMINAL_PASSWORD = \"plizen\"|TERMINAL_PASSWORD = \"$TERM_PASS\"|" "$PLIZEN_DIR/app.py"
ok "Terminal password set."

# ── Step 7: Set Pi IP in frontend ─────────────────────────────────────────
PI_IP=$(hostname -I | awk '{print $1}')
sed -i "s|const BACKEND = \".*\"|const BACKEND = \"http://${PI_IP}:9090\"|" "$PLIZEN_DIR/index.html"
ok "Backend URL set to http://${PI_IP}:9090"

# ── Step 8: Sudoers ────────────────────────────────────────────────────────
info "Configuring sudoers..."
echo "$PLIZEN_USER ALL=(ALL) NOPASSWD: /bin/systemctl start *
$PLIZEN_USER ALL=(ALL) NOPASSWD: /bin/systemctl stop *
$PLIZEN_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart *
$PLIZEN_USER ALL=(ALL) NOPASSWD: /sbin/reboot
$PLIZEN_USER ALL=(ALL) NOPASSWD: /sbin/shutdown" | sudo tee /etc/sudoers.d/plizen > /dev/null
sudo chmod 0440 /etc/sudoers.d/plizen
ok "Sudoers configured."

# ── Step 9: Fan udev rule ──────────────────────────────────────────────────
info "Setting up fan control permissions..."
echo 'SUBSYSTEM=="hwmon", ATTR{name}=="pwmfan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"
SUBSYSTEM=="hwmon", ATTR{name}=="rpi-pwm-fan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"' \
  | sudo tee /etc/udev/rules.d/99-plizen-fan.rules > /dev/null
sudo udevadm control --reload-rules && sudo udevadm trigger
ok "Fan udev rule installed."

# ── Step 10: Systemd services ──────────────────────────────────────────────
info "Installing systemd services..."

# Backend
sudo tee /etc/systemd/system/plizen.service > /dev/null << EOF
[Unit]
Description=Plizen — Pi Management Dashboard Backend
After=network.target

[Service]
User=$PLIZEN_USER
WorkingDirectory=$PLIZEN_DIR
ExecStart=$PLIZEN_DIR/venv/bin/python3 $PLIZEN_DIR/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Frontend
sudo tee /etc/systemd/system/plizen-ui.service > /dev/null << EOF
[Unit]
Description=Plizen — Pi Management Dashboard Frontend
After=network.target

[Service]
User=$PLIZEN_USER
WorkingDirectory=$PLIZEN_DIR
ExecStart=/usr/bin/python3 -m http.server 8080 --directory $PLIZEN_DIR
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable plizen plizen-ui
sudo systemctl restart plizen plizen-ui
ok "Services installed and started."

# ── Done ───────────────────────────────────────────────────────────────────
line
echo ""
echo -e "${GREEN}${BOLD}  ✅  Plizen v${PLIZEN_VERSION} installed successfully!${NC}"
echo ""
echo -e "  Open your browser and go to:"
echo -e "  ${CYAN}${BOLD}  http://${PI_IP}:8080${NC}"
echo ""
echo -e "  Backend API:  ${CYAN}http://${PI_IP}:9090${NC}"
echo ""
echo -e "  Service commands:"
echo -e "    ${YELLOW}sudo systemctl status plizen${NC}       → check backend"
echo -e "    ${YELLOW}sudo systemctl status plizen-ui${NC}    → check frontend"
echo -e "    ${YELLOW}sudo systemctl restart plizen${NC}      → restart backend"
echo -e "    ${YELLOW}journalctl -u plizen -f${NC}            → live backend logs"
echo ""
line
