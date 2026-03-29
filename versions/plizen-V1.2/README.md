# Plizen
### The open source Pi management dashboard
**Version 1.2 — Made by Dhruva**

![License](https://img.shields.io/badge/license-MIT-purple) ![Version](https://img.shields.io/badge/version-1.2-blueviolet) ![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red)

Plizen is a lightweight, self-hosted dashboard for your Raspberry Pi — monitor CPU, RAM, temperature, fan speed, storage, networking, services and logs from any browser on your local network.

---

## Features
- Live CPU, RAM, temperature and fan RPM (updates every 2 seconds)
- RPi Active Cooler control via hwmon sysfs (no GPIO library needed)
- Storage, networking, services and system logs
- Password-protected terminal (read-only safe commands)
- Fully customizable accent colors
- One-command installer

---

## Install

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/install.sh | bash
```

Then open your browser at `http://<your-pi-ip>:8080`

---

## Service commands

```bash
sudo systemctl status plizen        # check backend
sudo systemctl status plizen-ui     # check frontend
sudo systemctl restart plizen       # restart backend
sudo systemctl restart plizen-ui    # restart frontend
journalctl -u plizen -f             # live backend logs
```

---

## Requirements
- Raspberry Pi 4 or 5
- Raspberry Pi OS (Bullseye or Bookworm)
- Python 3.9+

---

## License
MIT — free to use, modify and share.

---

*Plizen v1.2 — by Dhruva*
