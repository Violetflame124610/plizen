<div align="center">

<img src="https://img.shields.io/badge/Plizen-v1.3-0ea47a?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/Platform-Raspberry%20Pi-red?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Open%20Source-Yes-blue?style=for-the-badge"/>

<br><br>

```
██████╗ ██╗     ██╗███████╗███████╗███╗   ██╗
██╔══██╗██║     ██║╚══███╔╝██╔════╝████╗  ██║
██████╔╝██║     ██║  ███╔╝ █████╗  ██╔██╗ ██║
██╔═══╝ ██║     ██║ ███╔╝  ██╔══╝  ██║╚██╗██║
██║     ███████╗██║███████╗███████╗██║ ╚████║
╚═╝     ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝
```

### The open source Pi management dashboard

Monitor your system, control your fan, manage services,<br>
configure your Pi — all from any browser on your network.<br>
**No cloud. No subscription. No nonsense.**

*Made with ❤️ by Dhruva*

<br>

[📦 Install](#-quick-install) · [✨ Features](#-features) · [📸 Screenshots](#-screenshots) · [📜 Versions](#-versions) · [🤝 Contribute](#-contributing)

---

</div>

## ⚡ Quick Install

```bash
cd ~ && curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.3/install.sh -o install.sh && bash install.sh
```

The installer will:
- Ask you to set a dashboard password
- Install all dependencies automatically
- Set up both services to auto-start on boot
- Tell you the URL to open when done

That's it. Open your browser and go to `http://<your-pi-ip>:9090`

---

## ✨ Features

### 🔐 Security
- Full screen login with your own custom password — set during install
- Session token system — auto logout after 30 minutes of inactivity
- Every API call is authenticated — nothing is accessible without login

### 📊 Monitoring
- Real-time CPU temperature with color coded alerts
- Per-core CPU usage with live sparkline charts
- RAM and Swap monitoring with gauges
- Disk usage across all mounted partitions
- Live network traffic per interface

### 🌀 Fan Control
- Full support for the official RPi Active Cooler
- Firmware auto mode — let the Pi manage it
- Manual PWM control — Off / Low / Med / High / Max
- Custom thermal curve editor

### ⚙️ Management
- Service manager — start, stop, restart any systemd service
- System journal logs with level filtering and search
- Software updates — see what packages need upgrading

### 🔧 Configure (raspi-config as GUI)
- Hostname change
- Enable / Disable SSH and VNC
- Toggle I2C, SPI, Serial, Camera interfaces
- Boot mode — CLI or Desktop
- GPU Memory split
- Timezone configuration

### ▸_ Terminal
- Full access shell from the browser
- Runs any command including sudo
- Color coded output — red for errors, white for normal

### 🎛️ Customization
- 4 accent color themes
- Teal accent by default (v1.3 signature color)

---

## 📸 Screenshots

<img width="1861" height="882" alt="image" src="https://github.com/user-attachments/assets/7fcbbf60-79a1-423e-9bc6-3d98cf2440f2" />


---

## 🖥️ Supported Hardware

| Device | Status |
|--------|--------|
| Raspberry Pi 5 | ✅ Fully supported |
| Raspberry Pi 4 Model B | ✅ Fully supported |
| Raspberry Pi 3 | ⚠️ Supported — no active cooler |
| Raspberry Pi Zero 2W | ⚠️ Supported — no active cooler |

---

## 📦 Requirements

- Raspberry Pi OS Bullseye or Bookworm
- Python 3.9 or higher
- Network connection
- A browser on the same network

---

## 🌀 Fan Control Setup

**Pi 5** — works out of the box, no extra steps needed.

**Pi 4** — enable the fan driver first:

```bash
echo "dtoverlay=rpi-pwm-fan" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

---

## 🔧 Manual Install

If you prefer to install manually without the script:

```bash
# 1. Install dependencies
pip install flask flask-cors flask-socketio --break-system-packages

# 2. Create directory
sudo mkdir -p /opt/plizen
sudo chown $(whoami):$(whoami) /opt/plizen

# 3. Download files
BASE="https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.3"
curl -sSL "$BASE/app.py" -o /opt/plizen/app.py
curl -sSL "$BASE/index.html" -o /opt/plizen/index.html

# 4. Set your password
echo "yourpassword" > /opt/plizen/.password
chmod 600 /opt/plizen/.password

# 5. Run
python3 /opt/plizen/app.py &
python3 -m http.server 9090 --directory /opt/plizen
```

---

## 🔑 Change Password

To change your dashboard password after install:

```bash
echo "yournewpassword" | sudo tee /opt/plizen/.password
sudo systemctl restart plizen
```

---

## 🛠️ Manage Services

```bash
# Check status
sudo systemctl status plizen
sudo systemctl status plizen-web

# Restart
sudo systemctl restart plizen plizen-web

# Stop
sudo systemctl stop plizen plizen-web

# View logs
journalctl -u plizen -f
```

---

## 📜 Versions

| Version | Highlights | Install |
|---------|-----------|---------|
| **v1.3** *(latest)* | Login screen, Configure tab, full terminal, auto logout | [Install v1.3](versions/plizen-V1.3/README.md) |
| v1.2 | Password protected terminal, fan control | [Install v1.2](versions/plizen-V1.2/README.md) |
| v1.1 | Passwordless, open terminal | [Install v1.1](versions/plizen-V1.1/README.md) |

---

## 🤝 Contributing

Pull requests are welcome! If you find a bug or want a new feature:

1. Fork the repo
2. Create a branch — `git checkout -b feature/your-feature`
3. Commit your changes
4. Push and open a Pull Request

Ideas for future versions:
- Docker container support
- Mobile responsive layout
- Email / webhook alerts on high temp
- Multi-Pi support
- Dark / light theme toggle

---

## 📄 License

MIT License — free to use, modify, and distribute.
Just keep the credits. 😊

---

<div align="center">

**Plizen v1.3** · Made by Dhruva · [GitHub](https://github.com/Violetflame124610/plizen)

*The open source Pi management dashboard*

⭐ If you find this useful, star the repo!

</div>
