<div align="center">

<img src="https://img.shields.io/badge/Plizen-v1.2-1f6feb?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/Terminal-Password%20Protected-green?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge"/>

# Plizen v1.2
### Latest Stable Release

> ✅ **This is the current recommended version.**  
> Terminal is protected with your real Raspberry Pi login credentials.  
> Same username and password as SSH.

*Made with ❤️ by Dhruva*

---

</div>

## ⚡ Quick Install (One Command)

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/install.sh | bash
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
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/app.py -o app.py
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/index.html -o index.html
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
# Download service files
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/versions/plizen-V1.2/install.sh | bash
```

Or manually:

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

## 🔐 Terminal Authentication

The terminal tab uses your **real Raspberry Pi login credentials** — same username and password you use for SSH. No separate password to remember.

---

## ✨ What's in v1.2

- 🌡️ Real-time CPU temperature with alerts
- ⚡ Per-core CPU usage with live charts
- 🧠 RAM & Swap monitoring
- 🌀 RPi Active Cooler control (firmware auto or manual)
- 💾 Storage overview
- 🌐 Network traffic monitoring
- ⚙️ Service manager — start, stop, restart
- 📋 System journal logs with filtering
- 🔄 Software updates checker
- 🖥️ Password protected terminal (real Pi credentials)
- 🎛️ Customizable accent colors and thermal curve

---

## 🔽 Looking for the passwordless version?

→ [Plizen v1.1](../plizen-V1.1/README.md) — open terminal, no login required

---

## 📄 License

MIT License — free to use, modify, and distribute.  
Just keep the credits. 😊

---

<div align="center">

**Plizen v1.2** · Made by Dhruva · [GitHub](https://github.com/Violetflame124610/plizen)

*The open source Pi management dashboard*

</div>
