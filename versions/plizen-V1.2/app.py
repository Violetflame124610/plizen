#!/usr/bin/env python3
"""
 ____  _  _  ____  ____  ____  _  _ 
(  _ \( )( )(_  _)(_   )( ___)( \( )
 ) __/ )()( _)(_   / /_  )__)  )  ( 
(__)  \____/(____) (____)(____)(_)\_)

Plizen — The open source Pi management dashboard
Version: 1.2
Author:  Dhruva
GitHub:  https://github.com/Violetflame124610/plizen

Supports the official Raspberry Pi Active Cooler (Pi 4 / Pi 5).
Fan speed is read and controlled via the kernel hwmon sysfs interface.
"""

import os, re, glob, time, subprocess, threading, json
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# ── Plizen config ──────────────────────────────────────────────────────────
PLIZEN_VERSION = "1.2"
PLIZEN_AUTHOR  = "Dhruva"

# Terminal password — change this after install
TERMINAL_PASSWORD = "plizen"

app = Flask(__name__)
app.config["SECRET_KEY"] = "plizen-secret-key"
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── RPi Active Cooler — hwmon sysfs ───────────────────────────────────────
FAN_HWMON_NAMES = {"rpi-pwm-fan", "pwmfan", "cooling_fan"}

fan_state = {
    "hwmon_path":  None,
    "pwm_file":    None,
    "rpm_file":    None,
    "enable_file": None,
    "name":        "RPi Active Cooler",
    "pct":         None,
    "auto":        True,
}

THERMAL_CURVE = {0: 0, 45: 25, 55: 50, 65: 75, 75: 90, 80: 100}


def find_fan_hwmon() -> bool:
    for hwmon in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        try:
            name = Path(os.path.join(hwmon, "name")).read_text().strip()
        except OSError:
            continue
        if name in FAN_HWMON_NAMES:
            fan_state["hwmon_path"]  = hwmon
            fan_state["pwm_file"]    = os.path.join(hwmon, "pwm1")
            fan_state["rpm_file"]    = os.path.join(hwmon, "fan1_input")
            fan_state["enable_file"] = os.path.join(hwmon, "pwm1_enable")
            fan_state["name"]        = name
            print(f"[Plizen] Active cooler found at {hwmon}  (driver: {name})")
            return True
    print("[Plizen] Active cooler not found in /sys/class/hwmon")
    return False


def read_fan_rpm() -> int:
    try:
        return int(Path(fan_state["rpm_file"]).read_text().strip())
    except Exception:
        return 0


def read_fan_pwm_raw() -> int:
    try:
        return int(Path(fan_state["pwm_file"]).read_text().strip())
    except Exception:
        return 0


def write_fan_pwm(duty_pct: int):
    if not fan_state["pwm_file"]:
        return
    raw = max(0, min(255, int(duty_pct / 100 * 255)))
    try:
        Path(fan_state["enable_file"]).write_text("1")
        Path(fan_state["pwm_file"]).write_text(str(raw))
        fan_state["pct"]  = duty_pct
        fan_state["auto"] = False
    except PermissionError:
        print("[Plizen] Permission denied writing pwm — add udev rule.")
    except Exception as e:
        print(f"[Plizen] write_fan_pwm error: {e}")


def set_fan_firmware_auto():
    if not fan_state["enable_file"]:
        return
    try:
        Path(fan_state["enable_file"]).write_text("2")
        fan_state["auto"] = True
        fan_state["pct"]  = None
    except Exception as e:
        print(f"[Plizen] set_fan_firmware_auto error: {e}")


def fan_info() -> dict:
    rpm      = read_fan_rpm() if fan_state["rpm_file"] else 0
    raw      = read_fan_pwm_raw() if fan_state["pwm_file"] else 0
    live_pct = round(raw / 255 * 100)
    return {
        "name":      fan_state["name"],
        "rpm":       rpm,
        "pct":       fan_state["pct"] if fan_state["pct"] is not None else live_pct,
        "auto":      fan_state["auto"],
        "available": fan_state["hwmon_path"] is not None,
    }


def curve_speed(temp: float) -> int:
    temps = sorted(THERMAL_CURVE.keys())
    if temp <= temps[0]:  return THERMAL_CURVE[temps[0]]
    if temp >= temps[-1]: return THERMAL_CURVE[temps[-1]]
    for i in range(len(temps) - 1):
        lo, hi = temps[i], temps[i + 1]
        if lo <= temp < hi:
            frac = (temp - lo) / (hi - lo)
            return int(THERMAL_CURVE[lo] + frac * (THERMAL_CURVE[hi] - THERMAL_CURVE[lo]))
    return 50


# ── System readers ─────────────────────────────────────────────────────────
def read_cpu_temp() -> float:
    try:
        return round(int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000.0, 1)
    except Exception:
        pass
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True, timeout=2)
        m = re.search(r"[\d.]+", out)
        return float(m.group()) if m else 0.0
    except Exception:
        return 0.0


def read_cpu_usage() -> dict:
    def parse():
        cores = {}
        for line in Path("/proc/stat").read_text().splitlines():
            if not line.startswith("cpu"): continue
            p    = line.split()
            vals = list(map(int, p[1:]))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            cores[p[0]] = (idle, sum(vals))
        return cores
    s1 = parse(); time.sleep(0.2); s2 = parse()
    result = {}
    for k in s1:
        d_total = (s2[k][1] - s1[k][1]) or 1
        d_idle  = s2[k][0] - s1[k][0]
        result[k] = round(100 * (1 - d_idle / d_total), 1)
    return result


def read_ram() -> dict:
    info = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":")
        info[k.strip()] = int(v.strip().split()[0])
    total = info.get("MemTotal", 1)
    free  = info.get("MemAvailable", 0)
    used  = total - free
    st    = info.get("SwapTotal", 0)
    sf    = info.get("SwapFree", 0)
    return {
        "total_mb":      round(total / 1024, 1),
        "used_mb":       round(used / 1024, 1),
        "free_mb":       round(free / 1024, 1),
        "pct":           round(used / total * 100, 1),
        "swap_total_mb": round(st / 1024, 1),
        "swap_used_mb":  round((st - sf) / 1024, 1),
        "swap_pct":      round((st - sf) / st * 100, 1) if st else 0,
    }


def read_disk() -> list:
    try:
        out = subprocess.check_output(
            ["df", "-h", "--output=source,target,fstype,size,used,avail,pcent"],
            text=True, timeout=5)
        rows = []
        for line in out.strip().splitlines()[1:]:
            p = line.split()
            if len(p) >= 7 and not p[0].startswith("tmpfs") and not p[0].startswith("udev"):
                rows.append({"device": p[0], "mount": p[1], "fstype": p[2],
                              "size": p[3], "used": p[4], "avail": p[5],
                              "pct": p[6].replace("%", "")})
        return rows
    except Exception:
        return []


def read_network() -> dict:
    stats = {}
    try:
        for line in Path("/proc/net/dev").read_text().splitlines()[2:]:
            p     = line.split()
            iface = p[0].rstrip(":")
            if iface == "lo": continue
            stats[iface] = {"rx_bytes": int(p[1]), "tx_bytes": int(p[9])}
    except Exception:
        pass
    return stats

_net_prev      = {}
_net_prev_time = time.time()

def calc_net_speed() -> dict:
    global _net_prev, _net_prev_time
    now     = time.time()
    cur     = read_network()
    elapsed = now - _net_prev_time or 1
    speeds  = {}
    for iface, data in cur.items():
        prev = _net_prev.get(iface, data)
        speeds[iface] = {
            "rx_kbps": round(max(0, data["rx_bytes"] - prev["rx_bytes"]) / elapsed / 1024, 1),
            "tx_kbps": round(max(0, data["tx_bytes"] - prev["tx_bytes"]) / elapsed / 1024, 1),
        }
    _net_prev      = cur
    _net_prev_time = now
    return speeds


def read_uptime() -> str:
    try:
        secs    = float(Path("/proc/uptime").read_text().split()[0])
        d, h, m = int(secs // 86400), int((secs % 86400) // 3600), int((secs % 3600) // 60)
        return f"{d}d {h}h {m}m"
    except Exception:
        return "unknown"

def read_hostname() -> str:
    try:    return Path("/etc/hostname").read_text().strip()
    except: return "raspberrypi"

def read_os_info() -> str:
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME"):
                return line.split("=")[1].strip().strip('"')
    except: pass
    return "Raspberry Pi OS"

def read_services() -> list:
    names  = ["ssh", "nginx", "bluetooth", "cron", "avahi-daemon",
               "cups", "ufw", "NetworkManager"]
    result = []
    for svc in names:
        try:
            status = subprocess.check_output(
                ["systemctl", "is-active", f"{svc}.service"],
                text=True, timeout=3).strip()
        except subprocess.CalledProcessError as e:
            status = (e.output or "inactive").strip()
        except:
            status = "unknown"
        try:
            pid = subprocess.check_output(
                ["systemctl", "show", f"{svc}.service",
                 "--property=MainPID", "--value"],
                text=True, timeout=3).strip()
            pid = pid if pid != "0" else "—"
        except:
            pid = "—"
        result.append({"name": f"{svc}.service", "status": status, "pid": pid})
    return result

def read_journal_logs(n=100) -> list:
    try:
        out = subprocess.check_output(
            ["journalctl", "-n", str(n), "--no-pager",
             "-o", "json-short", "--priority=7"],
            text=True, timeout=5)
        lvl_map = {"0": "emerg", "1": "alert", "2": "crit", "3": "err",
                   "4": "warn",  "5": "notice", "6": "info", "7": "debug"}
        entries = []
        for line in out.strip().splitlines():
            try:
                j = json.loads(line)
                entries.append({
                    "time":    j.get("__REALTIME_TIMESTAMP", "")[:19],
                    "level":   lvl_map.get(j.get("PRIORITY", "6"), "info"),
                    "message": j.get("MESSAGE", ""),
                    "unit":    j.get("_SYSTEMD_UNIT", "kernel"),
                })
            except: pass
        return entries
    except: return []

def read_updates() -> list:
    try:
        out = subprocess.check_output(
            ["apt-get", "--simulate", "upgrade"],
            text=True, stderr=subprocess.DEVNULL, timeout=30)
        updates = []
        for line in out.splitlines():
            if line.startswith("Inst "):
                p = line.split()
                updates.append({"package": p[1],
                                 "current": p[2].strip("[]") if len(p) > 2 else "?",
                                 "new":     p[3].strip("()") if len(p) > 3 else "?"})
        return updates
    except: return []

def get_ip_addresses() -> dict:
    ips = {}
    try:
        out = subprocess.check_output(["ip", "-4", "addr", "show"],
                                       text=True, timeout=5)
        iface = None
        for line in out.splitlines():
            m = re.match(r"^\d+: (\w+):", line)
            if m: iface = m.group(1)
            m2 = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", line)
            if m2 and iface: ips[iface] = m2.group(1)
    except: pass
    return ips


# ── API routes ─────────────────────────────────────────────────────────────
@app.route("/api/version")
def api_version():
    return jsonify({"name": "Plizen", "version": PLIZEN_VERSION,
                    "author": PLIZEN_AUTHOR,
                    "tagline": "The open source Pi management dashboard"})

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "temp":   read_cpu_temp(),
        "cpu":    read_cpu_usage(),
        "ram":    read_ram(),
        "uptime": read_uptime(),
        "fan":    fan_info(),
        "net":    calc_net_speed(),
    })

@app.route("/api/system")
def api_system():
    return jsonify({"hostname": read_hostname(), "os": read_os_info(),
                    "ips": get_ip_addresses(), "uptime": read_uptime()})

@app.route("/api/disk")
def api_disk():
    return jsonify({"disks": read_disk()})

@app.route("/api/services")
def api_services():
    return jsonify({"services": read_services()})

@app.route("/api/logs")
def api_logs():
    return jsonify({"logs": read_journal_logs(request.args.get("n", 100, type=int))})

@app.route("/api/updates")
def api_updates():
    return jsonify({"updates": read_updates()})

@app.route("/api/fan", methods=["POST"])
def api_set_fan():
    data = request.get_json()
    pct  = data.get("pct")
    auto = data.get("auto")
    if auto is True:
        set_fan_firmware_auto()
    elif pct is not None:
        write_fan_pwm(int(pct))
    return jsonify({"ok": True, "fan": fan_info()})

@app.route("/api/fan/curve", methods=["POST"])
def api_fan_curve():
    global THERMAL_CURVE
    curve = request.get_json().get("curve", {})
    THERMAL_CURVE = {int(k): int(v) for k, v in curve.items()}
    return jsonify({"ok": True, "curve": THERMAL_CURVE})

@app.route("/api/service/<action>/<name>", methods=["POST"])
def api_service_action(action, name):
    if action not in ("start", "stop", "restart"):
        return jsonify({"error": "Invalid action"}), 400
    name = re.sub(r"[^a-zA-Z0-9._-]", "", name)
    try:
        subprocess.run(["sudo", "systemctl", action, f"{name}.service"],
                       check=True, timeout=10)
        return jsonify({"ok": True})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

# ── Terminal — simple password auth ───────────────────────────────────────
ALLOWED_COMMANDS = {
    "uname -a", "ls", "ls -la", "pwd", "whoami", "uptime", "df -h", "free -h",
    "vcgencmd measure_temp", "cat /proc/cpuinfo", "hostname", "ip addr",
    "ps aux", "date",
}

@app.route("/api/exec", methods=["POST"])
def api_exec():
    data     = request.get_json()
    cmd      = data.get("cmd", "").strip()
    password = data.get("password", "")

    if password != TERMINAL_PASSWORD:
        return jsonify({"error": "Access denied: wrong password"}), 403

    if cmd not in ALLOWED_COMMANDS:
        return jsonify({"error": f"Command not allowed: {cmd}"}), 403

    try:
        out = subprocess.check_output(
            cmd.split(), text=True, timeout=10, stderr=subprocess.STDOUT)
        return jsonify({"output": out})
    except subprocess.CalledProcessError as e:
        return jsonify({"output": e.output or "Error"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reboot", methods=["POST"])
def api_reboot():
    threading.Timer(2, lambda: os.system("sudo reboot")).start()
    return jsonify({"ok": True})

@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    threading.Timer(2, lambda: os.system("sudo shutdown -h now")).start()
    return jsonify({"ok": True})


# ── WebSocket broadcast ────────────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print(f"[Plizen] Client connected: {request.sid}")
    emit("connected", {"status": "ok"})

def broadcast_stats():
    while True:
        try:
            socketio.emit("stats", {
                "temp":   read_cpu_temp(),
                "cpu":    read_cpu_usage(),
                "ram":    read_ram(),
                "uptime": read_uptime(),
                "fan":    fan_info(),
                "net":    calc_net_speed(),
            })
        except Exception as e:
            print(f"[Plizen] Broadcast error: {e}")
        time.sleep(2)


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("""
 ____  _    _  ____  ____  ____  _  _ 
(  _ \( )  ( )(_  _)(_   )( ___)( \( )
 ) __/ )()( _)  )(   / /_  )__)  )  ( 
(__)  \____/(__)(__)(____)(____)(_)\\_)

  The open source Pi management dashboard
  Version {ver} — by {author}
  GitHub: https://github.com/Violetflame124610/plizen
""".format(ver=PLIZEN_VERSION, author=PLIZEN_AUTHOR))

    find_fan_hwmon()
    if fan_state["enable_file"]:
        set_fan_firmware_auto()
    threading.Thread(target=broadcast_stats, daemon=True).start()
    print(f"[Plizen] Dashboard → http://0.0.0.0:9090")
    socketio.run(app, host="0.0.0.0", port=9090, debug=False, allow_unsafe_werkzeug=True)
