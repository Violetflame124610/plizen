<div align="center">

<img src="https://img.shields.io/badge/Plizen-v1.1-blue?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/Terminal-Open%20Access-yellow?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge"/>

# Plizen v1.1
### Passwordless Edition

> ⚠️ **This is the v1.1 passwordless release.**  
> The terminal has no authentication — anyone on your network can run commands.  
> Only use this on a **private trusted network**.  
> For the secure version, use [v1.2](../plizen-V1.2/README.md).

*Made with ❤️ by Dhruva*

---

</div>

## ⚡ Quick Install (One Command)

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.1/install.sh | bash
```

---

## 🔧 Manual Install

### Step 1 — Install dependencies

```bash
pip install flask flask-cors flask-socketio --break-system-packages
```

### Step 2 — Download the files

```bash
mkdir ~/plizen && cd ~/plizen
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.1/app.py -o app.py
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.1/index.html -o index.html
```

### Step 3 — Edit the backend URL in index.html

Open `index.html` and find this line near the top of the script:

```javascript
const BACKEND = "http://192.168.0.2:5000";
```

Change the IP to your Pi's actual IP address.

### Step 4 — Run the backend

```bash
python3 app.py
```

### Step 5 — Serve the frontend (new terminal)

```bash
python3 -m http.server 9090 --directory ~/plizen
```

### Step 6 — Open in browser

```
http://<your-pi-ip>:9090
```

---

## 🚀 Run as Services (Auto-start on boot)

```bash
sudo nano /etc/systemd/system/plizen.service
```

Paste:
```ini
[Unit]
Description=Plizen Backend
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/plizen
ExecStart=/usr/bin/python3 /home/pi/plizen/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo nano /etc/systemd/system/plizen-web.service
```

Paste:
```ini
[Unit]
Description=Plizen Web UI
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/plizen
ExecStart=/usr/bin/python3 -m http.server 9090 --directory /home/pi/plizen
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable plizen plizen-web
sudo systemctl start plizen plizen-web
```

Manage with:
```bash
sudo systemctl status plizen
sudo systemctl restart plizen
sudo systemctl stop plizen
```

---

## 🌀 Fan Control Setup

**Pi 5** — works out of the box, no extra steps.

**Pi 4** — enable the fan driver first:
```bash
echo "dtoverlay=rpi-pwm-fan" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

Then set permissions:
```bash
echo 'SUBSYSTEM=="hwmon", ATTR{name}=="pwmfan", RUN+="/bin/chmod 666 %S%p/pwm1 %S%p/pwm1_enable"' | sudo tee /etc/udev/rules.d/99-plizen-fan.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## ✨ What's in v1.1

- 🌡️ Real-time CPU temperature with alerts
- ⚡ Per-core CPU usage with live charts
- 🧠 RAM & Swap monitoring
- 🌀 RPi Active Cooler control (firmware auto or manual)
- 💾 Storage overview
- 🌐 Network traffic monitoring
- ⚙️ Service manager — start, stop, restart
- 📋 System journal logs with filtering
- 🔄 Software updates checker
- 🖥️ Open terminal (no password required)
- 🎛️ Customizable accent colors and thermal curve

---

## 🔼 Upgrade to v1.2

Get the secure version with real Pi login for the terminal:

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/install.sh | bash
```

---

## 📄 License

MIT License — free to use, modify, and distribute.  
Just keep the credits. 😊

---

<div align="center">

**Plizen v1.1** · Made by Dhruva · [GitHub](https://github.com/Violetflame124610/plizen)

*The open source Pi management dashboard*

</div>
