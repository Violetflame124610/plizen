<div align="center">

<img src="https://img.shields.io/badge/Plizen-v1.3-orange?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/Platform-Raspberry%20Pi-red?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Open%20Source-Yes-brightgreen?style=for-the-badge"/>

# 🥧 Plizen
### The open source Pi management dashboard

**Plizen** is a lightweight, self-hosted web dashboard for your Raspberry Pi.  
Monitor your system, control your fan, manage services, and more — all from any browser on your network.  
No cloud. No subscription. No nonsense.

*Made with ❤️ by Dhruva*

---

</div>

## ✨ Features

- 🌡️ **Real-time CPU temperature** with color-coded alerts
- ⚡ **Per-core CPU usage** with live history charts
- 🧠 **RAM & Swap monitoring**
- 🌀 **RPi Active Cooler control** — firmware auto or manual PWM
- 💾 **Storage overview** across all mounted disks
- 🌐 **Network traffic** — live RX/TX per interface
- ⚙️ **Service manager** — start, stop, restart systemd services
- 📋 **System journal logs** with filtering
- 🔄 **Software updates** — see what packages need updating
- 🖥️ **Terminal** — safe read-only shell with password protection
- 🎛️ **Fully customizable** — accent colors, thermal curve, toggles
- 🚀 **One command install** — just like Pi-hole

---

## ⚡ Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/install.sh | bash
```

That's it. Plizen will install itself, set up both services, and tell you the URL to open.

---

## 🖥️ Supported Hardware

| Device | Status |
|--------|--------|
| Raspberry Pi 5 | ✅ Fully supported |
| Raspberry Pi 4 Model B | ✅ Fully supported |
| Raspberry Pi 3 | ⚠️ Supported (no active cooler) |
| Raspberry Pi Zero 2W | ⚠️ Supported (no active cooler) |

---

## 📦 Requirements

- Raspberry Pi OS (Bullseye or Bookworm)
- Python 3.9+
- Network connection
- A browser on the same network

---

## 🌐 Access

After install, open your browser and go to:

```
http://<your-pi-ip>:9090
```

Or if mDNS is enabled:

```
http://raspberrypi.local:9090
```

---

## 🗂️ Project Structure

```
plizen/
├── app.py              # Flask backend — reads system data, controls fan
├── index.html          # Frontend dashboard — single file, no build needed
├── install.sh          # One-command installer
├── plizen.service      # Systemd service file (backend)
├── plizen-web.service  # Systemd service file (frontend)
└── README.md
```

---

## 🔧 Manual Install

If you prefer to install manually:

```bash
# 1. Clone the repo
git clone https://github.com/Violetflame124610/plizen.git
cd plizen

# 2. Install dependencies
pip install flask flask-cors flask-socketio --break-system-packages

# 3. Run the backend
python3 app.py

# 4. In a second terminal, serve the frontend
python3 -m http.server 9090 --directory .
```

---

## 🌀 Fan Control

Plizen supports the **official Raspberry Pi Active Cooler** out of the box.  
It reads and controls the fan via the kernel's `hwmon` sysfs interface — no GPIO library needed.

For Pi 4, enable the fan driver first:
```bash
echo "dtoverlay=rpi-pwm-fan" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

Pi 5 users — the fan works out of the box, no extra steps.

---

## 📜 Versions

| Version | Description |
|---------|-------------|
| [v1.2](https://github.com/Violetflame124610/plizen) | Current — password protected terminal, fan control, full dashboard |
| [v1.1](https://github.com/Violetflame124610/plizen/tree/v1.1) | Passwordless version — open access terminal |

---

## 🤝 Contributing

Pull requests are welcome! If you find a bug or want a new feature:

1. Fork the repo
2. Create a branch (`git checkout -b feature/cool-thing`)
3. Commit your changes
4. Push and open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.  
Just keep the credits. 😊

---

<div align="center">

**Plizen v1.2** · Made by Dhruva · [GitHub](https://github.com/Violetflame124610/plizen)

*The open source Pi management dashboard*<br>
[Explore more in the website!!](https://plizen.pythonanywhere.com)
</div>
