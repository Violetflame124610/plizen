#!/usr/bin/env python3
"""
Plizen v1.3 Backend
Simple password login — set during install.
Made by Dhruva — github.com/Violetflame124610/plizen
"""

import os, re, glob, time, subprocess, threading, json, secrets
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# ── Password ───────────────────────────────────────────────────────────────
DASHBOARD_PASSWORD_FILE = "/opt/plizen/.password"

def get_password() -> str:
    try:
        return Path(DASHBOARD_PASSWORD_FILE).read_text().strip()
    except:
        return ""

def check_password(pwd: str) -> bool:
    stored = get_password()
    return bool(stored) and pwd == stored

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Sessions ───────────────────────────────────────────────────────────────
SESSIONS = {}
SESSION_TIMEOUT = 30 * 60

def new_session() -> str:
    token = secrets.token_hex(32)
    SESSIONS[token] = {"last_active": time.time()}
    return token

def get_session(token: str):
    s = SESSIONS.get(token)
    if not s: return None
    if time.time() - s["last_active"] > SESSION_TIMEOUT:
        del SESSIONS[token]; return None
    s["last_active"] = time.time()
    return s

def auth():
    token = request.headers.get("X-Plizen-Token")
    if not token:
        try: token = (request.get_json(silent=True) or {}).get("token")
        except: pass
    return get_session(token)

def cleanup_sessions():
    while True:
        now = time.time()
        for t in [t for t, s in list(SESSIONS.items()) if now - s["last_active"] > SESSION_TIMEOUT]:
            del SESSIONS[t]
        time.sleep(60)

# ── RPi Active Cooler ──────────────────────────────────────────────────────
FAN_HWMON_NAMES = {"rpi-pwm-fan", "pwmfan", "cooling_fan"}
fan_state = {"hwmon_path": None, "pwm_file": None, "rpm_file": None,
             "enable_file": None, "name": "RPi Active Cooler", "pct": None, "auto": True}
THERMAL_CURVE = {0: 0, 45: 25, 55: 50, 65: 75, 75: 90, 80: 100}

def find_fan_hwmon():
    for hwmon in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        try:
            name = Path(os.path.join(hwmon, "name")).read_text().strip()
        except OSError:
            continue
        if name in FAN_HWMON_NAMES:
            fan_state.update({"hwmon_path": hwmon,
                "pwm_file": os.path.join(hwmon, "pwm1"),
                "rpm_file": os.path.join(hwmon, "fan1_input"),
                "enable_file": os.path.join(hwmon, "pwm1_enable"),
                "name": name})
            print(f"[OK] Fan: {hwmon} ({name})")
            return True
    print("[WARN] Active cooler not found")
    return False

def read_fan_rpm():
    try: return int(Path(fan_state["rpm_file"]).read_text().strip())
    except: return 0

def read_fan_pwm_raw():
    try: return int(Path(fan_state["pwm_file"]).read_text().strip())
    except: return 0

def write_fan_pwm(pct: int):
    if not fan_state["pwm_file"]: return
    raw = max(0, min(255, int(pct / 100 * 255)))
    try:
        Path(fan_state["enable_file"]).write_text("1")
        Path(fan_state["pwm_file"]).write_text(str(raw))
        fan_state["pct"] = pct; fan_state["auto"] = False
    except Exception as e: print(f"[ERR] fan pwm: {e}")

def set_fan_auto():
    if not fan_state["enable_file"]: return
    try:
        Path(fan_state["enable_file"]).write_text("2")
        fan_state["auto"] = True; fan_state["pct"] = None
    except Exception as e: print(f"[ERR] fan auto: {e}")

def fan_info():
    rpm = read_fan_rpm() if fan_state["rpm_file"] else 0
    raw = read_fan_pwm_raw() if fan_state["pwm_file"] else 0
    return {"name": fan_state["name"], "rpm": rpm,
            "pct": fan_state["pct"] if fan_state["pct"] is not None else round(raw / 255 * 100),
            "auto": fan_state["auto"], "available": fan_state["hwmon_path"] is not None}

# ── System readers ─────────────────────────────────────────────────────────
def read_cpu_temp():
    try: return round(int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000.0, 1)
    except: pass
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True, timeout=2)
        m = re.search(r"[\d.]+", out)
        return float(m.group()) if m else 0.0
    except: return 0.0

def read_cpu_usage():
    def parse():
        cores = {}
        for line in Path("/proc/stat").read_text().splitlines():
            if not line.startswith("cpu"): continue
            p = line.split(); vals = list(map(int, p[1:]))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            cores[p[0]] = (idle, sum(vals))
        return cores
    s1 = parse(); time.sleep(0.2); s2 = parse()
    return {k: round(100 * (1 - (s2[k][0] - s1[k][0]) / ((s2[k][1] - s1[k][1]) or 1)), 1) for k in s1}

def read_ram():
    info = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":"); info[k.strip()] = int(v.strip().split()[0])
    total = info.get("MemTotal", 1); free = info.get("MemAvailable", 0); used = total - free
    st = info.get("SwapTotal", 0); sf = info.get("SwapFree", 0)
    return {"total_mb": round(total/1024,1), "used_mb": round(used/1024,1),
            "free_mb": round(free/1024,1), "pct": round(used/total*100,1),
            "swap_total_mb": round(st/1024,1), "swap_used_mb": round((st-sf)/1024,1),
            "swap_pct": round((st-sf)/st*100,1) if st else 0}

def read_disk():
    try:
        out = subprocess.check_output(["df","-h","--output=source,target,fstype,size,used,avail,pcent"], text=True, timeout=5)
        rows = []
        for line in out.strip().splitlines()[1:]:
            p = line.split()
            if len(p) >= 7 and not p[0].startswith("tmpfs") and not p[0].startswith("udev"):
                rows.append({"device":p[0],"mount":p[1],"fstype":p[2],"size":p[3],"used":p[4],"avail":p[5],"pct":p[6].replace("%","")})
        return rows
    except: return []

def read_network():
    stats = {}
    try:
        for line in Path("/proc/net/dev").read_text().splitlines()[2:]:
            p = line.split(); iface = p[0].rstrip(":")
            if iface == "lo": continue
            stats[iface] = {"rx_bytes": int(p[1]), "tx_bytes": int(p[9])}
    except: pass
    return stats

_net_prev = {}; _net_prev_time = time.time()
def calc_net_speed():
    global _net_prev, _net_prev_time
    now = time.time(); cur = read_network(); elapsed = now - _net_prev_time or 1
    speeds = {}
    for iface, data in cur.items():
        prev = _net_prev.get(iface, data)
        speeds[iface] = {"rx_kbps": round(max(0, data["rx_bytes"]-prev["rx_bytes"])/elapsed/1024, 1),
                         "tx_kbps": round(max(0, data["tx_bytes"]-prev["tx_bytes"])/elapsed/1024, 1)}
    _net_prev = cur; _net_prev_time = now; return speeds

def read_uptime():
    try:
        secs = float(Path("/proc/uptime").read_text().split()[0])
        d, h, m = int(secs//86400), int((secs%86400)//3600), int((secs%3600)//60)
        return f"{d}d {h}h {m}m"
    except: return "unknown"

def read_hostname():
    try: return Path("/etc/hostname").read_text().strip()
    except: return "raspberrypi"

def read_os_info():
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME"): return line.split("=")[1].strip().strip('"')
    except: pass
    return "Raspberry Pi OS"

def read_services():
    names = ["ssh","nginx","bluetooth","cron","avahi-daemon","cups","ufw","NetworkManager"]
    result = []
    for svc in names:
        try: status = subprocess.check_output(["systemctl","is-active",f"{svc}.service"], text=True, timeout=3).strip()
        except subprocess.CalledProcessError as e: status = (e.output or "inactive").strip()
        except: status = "unknown"
        try:
            pid = subprocess.check_output(["systemctl","show",f"{svc}.service","--property=MainPID","--value"], text=True, timeout=3).strip()
            pid = pid if pid != "0" else "—"
        except: pid = "—"
        result.append({"name": f"{svc}.service", "status": status, "pid": pid})
    return result

def read_journal_logs(n=100):
    try:
        out = subprocess.check_output(["journalctl","-n",str(n),"--no-pager","-o","json-short","--priority=7"], text=True, timeout=5)
        lvl = {"0":"emerg","1":"alert","2":"crit","3":"err","4":"warn","5":"notice","6":"info","7":"debug"}
        entries = []
        for line in out.strip().splitlines():
            try:
                j = json.loads(line)
                entries.append({"time":j.get("__REALTIME_TIMESTAMP","")[:19],"level":lvl.get(j.get("PRIORITY","6"),"info"),"message":j.get("MESSAGE",""),"unit":j.get("_SYSTEMD_UNIT","kernel")})
            except: pass
        return entries
    except: return []

def read_updates():
    try:
        out = subprocess.check_output(["apt-get","--simulate","upgrade"], text=True, stderr=subprocess.DEVNULL, timeout=30)
        updates = []
        for line in out.splitlines():
            if line.startswith("Inst "):
                p = line.split()
                updates.append({"package":p[1],"current":p[2].strip("[]") if len(p)>2 else "?","new":p[3].strip("()") if len(p)>3 else "?"})
        return updates
    except: return []

def get_ip_addresses():
    ips = {}
    try:
        out = subprocess.check_output(["ip","-4","addr","show"], text=True, timeout=5)
        iface = None
        for line in out.splitlines():
            m = re.match(r"^\d+: (\w+):", line)
            if m: iface = m.group(1)
            m2 = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", line)
            if m2 and iface: ips[iface] = m2.group(1)
    except: pass
    return ips

def get_configure_data():
    data = {}
    data["hostname"] = read_hostname()
    try:
        ssh = subprocess.check_output(["systemctl","is-active","ssh"], text=True, timeout=3).strip()
        data["ssh_enabled"] = ssh == "active"
    except: data["ssh_enabled"] = False
    try:
        vnc = subprocess.check_output(["systemctl","is-active","vncserver-x11-serviced"], text=True, timeout=3).strip()
        data["vnc_enabled"] = vnc == "active"
    except: data["vnc_enabled"] = False
    try: data["timezone"] = subprocess.check_output(["timedatectl","show","--property=Timezone","--value"], text=True, timeout=3).strip()
    except: data["timezone"] = "Unknown"
    try:
        loc = subprocess.check_output(["localectl","status"], text=True, timeout=3)
        m = re.search(r"System Locale: LANG=(.*)", loc)
        data["locale"] = m.group(1) if m else "Unknown"
    except: data["locale"] = "Unknown"
    try:
        wc = Path("/etc/wpa_supplicant/wpa_supplicant.conf").read_text()
        m = re.search(r"country=(\w+)", wc)
        data["wifi_country"] = m.group(1) if m else "Not set"
    except: data["wifi_country"] = "Not set"
    try:
        cfg = Path("/boot/firmware/config.txt").read_text()
        m = re.search(r"arm_freq=(\d+)", cfg)
        data["arm_freq"] = m.group(1) if m else "Default"
        m2 = re.search(r"gpu_freq=(\d+)", cfg)
        data["gpu_freq"] = m2.group(1) if m2 else "Default"
        data["camera_enabled"] = "camera_auto_detect=1" in cfg or "start_x=1" in cfg
        data["i2c_enabled"] = "dtparam=i2c_arm=on" in cfg
        data["spi_enabled"] = "dtparam=spi=on" in cfg
        data["serial_enabled"] = "enable_uart=1" in cfg
        m3 = re.search(r"gpu_mem=(\d+)", cfg)
        data["gpu_mem"] = m3.group(1) if m3 else "64"
    except:
        data["arm_freq"] = "Unknown"; data["gpu_freq"] = "Unknown"
        data["camera_enabled"] = False; data["i2c_enabled"] = False
        data["spi_enabled"] = False; data["serial_enabled"] = False
        data["gpu_mem"] = "64"
    try:
        bl = subprocess.check_output(["systemctl","get-default"], text=True, timeout=3).strip()
        data["boot_mode"] = "Desktop" if "graphical" in bl else "CLI"
    except: data["boot_mode"] = "Unknown"
    return data

# ── API Routes ─────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    password = data.get("password", "")
    if not password:
        return jsonify({"ok": False, "error": "Password required"}), 400
    if check_password(password):
        token = new_session()
        print(f"[OK] Login successful")
        return jsonify({"ok": True, "token": token})
    print(f"[WARN] Failed login attempt")
    return jsonify({"ok": False, "error": "Wrong password"}), 403

@app.route("/api/logout", methods=["POST"])
def api_logout():
    data = request.get_json() or {}
    token = data.get("token") or request.headers.get("X-Plizen-Token")
    if token and token in SESSIONS:
        del SESSIONS[token]
    return jsonify({"ok": True})

@app.route("/api/ping", methods=["POST"])
def api_ping():
    return jsonify({"ok": bool(auth())})

@app.route("/api/stats")
def api_stats():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"temp": read_cpu_temp(), "cpu": read_cpu_usage(),
                    "ram": read_ram(), "uptime": read_uptime(),
                    "fan": fan_info(), "net": calc_net_speed()})

@app.route("/api/system")
def api_system():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"hostname": read_hostname(), "os": read_os_info(),
                    "ips": get_ip_addresses(), "uptime": read_uptime()})

@app.route("/api/disk")
def api_disk():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"disks": read_disk()})

@app.route("/api/services")
def api_services():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"services": read_services()})

@app.route("/api/logs")
def api_logs():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"logs": read_journal_logs(request.args.get("n", 100, type=int))})

@app.route("/api/updates")
def api_updates():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"updates": read_updates()})

@app.route("/api/fan", methods=["POST"])
def api_set_fan():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if data.get("auto") is True: set_fan_auto()
    elif data.get("pct") is not None: write_fan_pwm(int(data["pct"]))
    return jsonify({"ok": True, "fan": fan_info()})

@app.route("/api/fan/curve", methods=["POST"])
def api_fan_curve():
    global THERMAL_CURVE
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    THERMAL_CURVE = {int(k): int(v) for k, v in request.get_json().get("curve", {}).items()}
    return jsonify({"ok": True})

@app.route("/api/service/<action>/<n>", methods=["POST"])
def api_service_action(action, name):
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    if action not in ("start", "stop", "restart"): return jsonify({"error": "Invalid"}), 400
    name = re.sub(r"[^a-zA-Z0-9._-]", "", name)
    try:
        subprocess.run(["sudo", "systemctl", action, f"{name}.service"], check=True, timeout=10)
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/configure")
def api_configure():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_configure_data())

@app.route("/api/configure/hostname", methods=["POST"])
def api_set_hostname():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    hostname = re.sub(r"[^a-zA-Z0-9-]", "", request.get_json().get("hostname", ""))
    if not hostname: return jsonify({"error": "Invalid hostname"}), 400
    try:
        subprocess.run(["sudo", "hostnamectl", "set-hostname", hostname], check=True, timeout=10)
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/configure/ssh", methods=["POST"])
def api_set_ssh():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    enable = request.get_json().get("enable", True)
    try:
        action = "enable --now" if enable else "disable --now"
        subprocess.run(f"sudo systemctl {action} ssh".split(), check=True, timeout=10)
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/configure/timezone", methods=["POST"])
def api_set_timezone():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    tz = request.get_json().get("timezone", "")
    if not tz: return jsonify({"error": "Timezone required"}), 400
    try:
        subprocess.run(["sudo", "timedatectl", "set-timezone", tz], check=True, timeout=10)
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/configure/boot", methods=["POST"])
def api_set_boot():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    mode = request.get_json().get("mode", "cli")
    target = "graphical.target" if mode == "desktop" else "multi-user.target"
    try:
        subprocess.run(["sudo", "systemctl", "set-default", target], check=True, timeout=10)
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/configure/interface", methods=["POST"])
def api_set_interface():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    iface = data.get("interface", "")
    enable = data.get("enable", True)
    cfg_map = {
        "i2c":    ("dtparam=i2c_arm=on",   "dtparam=i2c_arm=off"),
        "spi":    ("dtparam=spi=on",         "dtparam=spi=off"),
        "serial": ("enable_uart=1",          "enable_uart=0"),
        "camera": ("camera_auto_detect=1",   "camera_auto_detect=0"),
    }
    if iface not in cfg_map: return jsonify({"error": "Unknown interface"}), 400
    on_str, off_str = cfg_map[iface]
    target = on_str if enable else off_str
    remove = off_str if enable else on_str
    try:
        cfg_path = "/boot/firmware/config.txt"
        cfg = Path(cfg_path).read_text()
        if remove in cfg: cfg = cfg.replace(remove, target)
        elif target not in cfg: cfg += f"\n{target}\n"
        subprocess.run(["sudo", "tee", cfg_path], input=cfg, text=True, check=True, timeout=10)
        return jsonify({"ok": True, "note": "Reboot required"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/configure/gpu_mem", methods=["POST"])
def api_set_gpu_mem():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    mem = int(request.get_json().get("gpu_mem", 64))
    if mem not in [16, 32, 64, 128, 256]: return jsonify({"error": "Invalid value"}), 400
    try:
        cfg_path = "/boot/firmware/config.txt"
        cfg = Path(cfg_path).read_text()
        if re.search(r"gpu_mem=\d+", cfg): cfg = re.sub(r"gpu_mem=\d+", f"gpu_mem={mem}", cfg)
        else: cfg += f"\ngpu_mem={mem}\n"
        subprocess.run(["sudo", "tee", cfg_path], input=cfg, text=True, check=True, timeout=10)
        return jsonify({"ok": True, "note": "Reboot required"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# ── Terminal — full access ─────────────────────────────────────────────────
@app.route("/api/exec", methods=["POST"])
def api_exec():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    cmd = request.get_json().get("cmd", "").strip()
    if not cmd: return jsonify({"output": ""})
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            text=True, timeout=30,
            capture_output=True
        )
        output = result.stdout
        if result.stderr:
            output += result.stderr
        return jsonify({"output": output or "(command completed with no output)", "code": result.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Command timed out after 30 seconds", "code": -1})
    except Exception as e:
        return jsonify({"output": str(e), "code": -1})

@app.route("/api/reboot", methods=["POST"])
def api_reboot():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    threading.Timer(2, lambda: os.system("sudo reboot")).start()
    return jsonify({"ok": True})

@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    if not auth(): return jsonify({"error": "Unauthorized"}), 401
    threading.Timer(2, lambda: os.system("sudo shutdown -h now")).start()
    return jsonify({"ok": True})

# ── WebSocket ──────────────────────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print(f"[WS] Connected: {request.sid}")
    emit("connected", {"status": "ok"})

@socketio.on("authenticate")
def on_authenticate(data):
    s = get_session(data.get("token", ""))
    if s: emit("auth_ok", {})
    else: emit("auth_fail", {"error": "Session expired"})

def broadcast_stats():
    while True:
        try:
            if SESSIONS:
                socketio.emit("stats", {
                    "temp": read_cpu_temp(), "cpu": read_cpu_usage(),
                    "ram": read_ram(), "uptime": read_uptime(),
                    "fan": fan_info(), "net": calc_net_speed(),
                })
        except Exception as e:
            print(f"[ERR] broadcast: {e}")
        time.sleep(2)

# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    find_fan_hwmon()
    set_fan_auto()
    threading.Thread(target=broadcast_stats, daemon=True).start()
    threading.Thread(target=cleanup_sessions, daemon=True).start()
    print("[OK] Plizen v1.3 → http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
