import asyncio
import platform
import shutil
import socket
import subprocess
import time
from collections import deque
from typing import Optional

import psutil


class SystemService:
    def __init__(self):
        self._cpu_history: deque = deque(maxlen=120)
        self._ram_history: deque = deque(maxlen=120)
        self._last_cpu: float = 0.0
        self._last_ram: float = 0.0
        self._boot_time = psutil.boot_time()

    # ------------------------------------------------------------- raw stats
    def _cpu(self) -> dict:
        try:
            percent = psutil.cpu_percent(interval=None)
            self._last_cpu = float(percent)
            self._cpu_history.append({"time": time.time() * 1000, "value": self._last_cpu})
            freq = psutil.cpu_freq()
            cores = psutil.cpu_count(logical=True)
            return {
                "percent": self._last_cpu,
                "cores": cores,
                "freq_mhz": round(freq.current, 0) if freq else None,
                "load_avg": [round(x, 2) for x in psutil.getloadavg()],
            }
        except Exception as exc:
            return {"percent": None, "error": str(exc)}

    def _ram(self) -> dict:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            self._last_ram = float(mem.percent)
            self._ram_history.append({"time": time.time() * 1000, "value": self._last_ram})
            return {
                "percent": mem.percent,
                "used_gb": round(mem.used / (1024**3), 1),
                "total_gb": round(mem.total / (1024**3), 1),
                "available_gb": round(mem.available / (1024**3), 1),
                "swap_percent": swap.percent,
            }
        except Exception as exc:
            return {"percent": None, "error": str(exc)}

    def _disk(self) -> dict:
        try:
            root = psutil.disk_usage("/")
            home = psutil.disk_usage("/home") if psutil.disk_usage("/home").total > 0 else root
            return {
                "root_percent": root.percent,
                "root_total_gb": round(root.total / (1024**3), 1),
                "root_used_gb": round(root.used / (1024**3), 1),
                "home_percent": home.percent,
                "home_total_gb": round(home.total / (1024**3), 1),
                "home_used_gb": round(home.used / (1024**3), 1),
                "percent": max(root.percent, home.percent),
            }
        except Exception as exc:
            return {"percent": None, "error": str(exc)}

    def _battery(self) -> dict:
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {"present": False}
            return {
                "present": True,
                "percent": round(battery.percent, 1),
                "power_plugged": bool(battery.power_plugged),
                "seconds_left": battery.secsleft if battery.secsleft >= 0 else None,
            }
        except Exception:
            return {"present": False}

    def _gpu(self) -> dict:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().splitlines()[0].split(",")
                return {
                    "vendor": "nvidia",
                    "name": line[0].strip(),
                    "percent": float(line[1].strip()),
                    "memory_used_gb": round(float(line[2].strip()) / 1024, 1),
                    "memory_total_gb": round(float(line[3].strip()) / 1024, 1),
                    "temperature": float(line[4].strip()) if len(line) > 4 else None,
                }
        except Exception:
            pass
        return {"present": False, "name": "Intel iGPU (software)"}

    def _network(self) -> dict:
        try:
            interfaces = []
            for name, stats in psutil.net_if_stats().items():
                if name == "lo":
                    continue
                addrs = psutil.net_if_addrs().get(name, [])
                ip = next((a.address for a in addrs if a.family == socket.AF_INET), None)
                interfaces.append({
                    "name": name,
                    "isup": stats.isup,
                    "speed": stats.speed,
                    "ip": ip,
                })
            io = psutil.net_io_counters()
            return {"interfaces": interfaces, "bytes_sent": io.bytes_sent, "bytes_recv": io.bytes_recv}
        except Exception as exc:
            return {"error": str(exc), "interfaces": []}

    def _temperature(self) -> dict:
        try:
            temps = psutil.sensors_temperatures()
            out = []
            for sensor, values in temps.items():
                for v in values:
                    if v.current is not None:
                        out.append({"sensor": sensor, "label": v.label or "", "current": round(v.current, 1)})
            core = max((t["current"] for t in out if "coretemp" in t["sensor"] or "core" in t["label"].lower()), default=None)
            return {"sensors": out, "core_celsius": round(core, 1) if core is not None else None}
        except Exception:
            return {"sensors": [], "core_celsius": None}

    # ------------------------------------------------------------- snapshot
    def full_stats(self) -> dict:
        cpu = self._cpu()
        ram = self._ram()
        return {
            "cpu": cpu,
            "ram": ram,
            "disk": self._disk(),
            "battery": self._battery(),
            "gpu": self._gpu(),
            "network": self._network(),
            "temperature": self._temperature(),
            "uptime": {"seconds": int(time.time() - self._boot_time)},
            "os": {
                "name": platform.system(),
                "distro": platform.freedesktop_os_release().get("PRETTY_NAME", "Linux") if hasattr(platform, "freedesktop_os_release") else "Linux",
                "version": platform.release(),
                "kernel": platform.platform(),
                "machine": platform.machine(),
                "hostname": socket.gethostname(),
            },
        }

    def get_history(self) -> dict:
        return {"cpu": list(self._cpu_history), "ram": list(self._ram_history)}

    # ------------------------------------------------------------- services
    async def check_pipewire(self) -> dict:
        try:
            result = await asyncio.to_thread(
                subprocess.run, ["pactl", "info"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return {"status": "online"}
            return {"status": "offline", "error": "pactl returned non-zero"}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    async def check_database(self, db_path: str) -> dict:
        try:
            import sqlite3

            conn = sqlite3.connect(db_path, timeout=2)
            conn.execute("SELECT 1")
            conn.close()
            return {"status": "online"}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    def check_microphone(self) -> dict:
        try:
            import speech_recognition as sr

            with sr.Microphone() as source:
                return {"status": "online", "device": getattr(source, "device_index", None)}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    def check_backend(self) -> dict:
        return {"status": "online"}

    def check_websocket(self, ws_manager) -> dict:
        return {"status": "online", "connections": getattr(ws_manager, "count", 0)}

    async def system_uptime_seconds(self) -> int:
        return int(time.time() - self._boot_time)

    async def os_name(self) -> str:
        try:
            if hasattr(platform, "freedesktop_os_release"):
                release = platform.freedesktop_os_release()
                return release.get("PRETTY_NAME", platform.system())
        except Exception:
            pass
        return platform.system()

    async def kernel_release(self) -> str:
        return platform.release()

    async def hostname(self) -> str:
        return socket.gethostname()


system_service = SystemService()
