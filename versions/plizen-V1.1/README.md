<div align="center">

<img src="https://img.shields.io/badge/Plizen-v1.1-blue?style=for-the-badge&logo=raspberry-pi&logoColor=white"/>
<img src="https://img.shields.io/badge/Terminal-Open%20Access-yellow?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>

# 🥧 Plizen v1.1
### Passwordless Edition

> ⚠️ **This is the v1.1 passwordless release.**  
> The terminal has no authentication — anyone on your network can run commands.  
> Only use this on a **private trusted network**.  
> For the secure version with password protection, use [v1.2](https://github.com/Violetflame124610/plizen).

*Made with ❤️ by Dhruva*

---

</div>

## ⚡ Quick Install (One Command)

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/versions/plizen-V1.1/install.sh | bash
```

---

## 🔧 Manual Install

### Step 1 — Clone the v1.1 branch

```bash
git clone --branch v1.1 https://github.com/Violetflame124610/plizen.git
cd plizen
```

### Step 2 — Install dependencies

```bash
pip install flask flask-cors flask-socketio --break-system-packages
```

### Step 3 — Run the backend

```bash
python3 app.py
```

### Step 4 — Serve the frontend (new terminal)

```bash
python3 -m http.server 9090 --directory .
```

### Step 5 — Open in browser

```
http://<your-pi-ip>:9090
```

---

## 🚀 Run as Services (Auto-start on boot)

```bash
# Copy service files
sudo cp plizen.service /etc/systemd/system/
sudo cp plizen-web.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable plizen plizen-web
sudo systemctl start plizen plizen-web
```

Check status:
```bash
sudo systemctl status plizen
sudo systemctl status plizen-web
```

---

## 🌀 Fan Control (Pi 4 only — Pi 5 works out of the box)

```bash
echo "dtoverlay=rpi-pwm-fan" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

---

## ✨ What's in v1.1

- 🌡️ Real-time CPU temperature
- ⚡ Per-core CPU usage with live charts
- 🧠 RAM & Swap monitoring
- 🌀 RPi Active Cooler control
- 💾 Storage overview
- 🌐 Network traffic monitoring
- ⚙️ Service manager
- 📋 System journal logs
- 🔄 Software updates checker
- 🖥️ Open terminal (no password)
- 🎛️ Customizable accent colors

---

## 🔼 Upgrade to v1.2

To get the secure version with password-protected terminal:

```bash
curl -sSL https://raw.githubusercontent.com/Violetflame124610/plizen/main/install.sh | bash
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
