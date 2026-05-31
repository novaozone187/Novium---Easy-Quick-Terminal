# system_monitor.py
import os
import psutil
import shutil
import time
from pathlib import Path


def get_system_stats_snapshot(psutil_lib=None):
    """Gathers a snapshot of key system metrics."""
    if psutil_lib is None:
        psutil_lib = psutil

    try:
        cpu_pct = psutil_lib.cpu_percent(interval=0.1)
        mem_info = psutil_lib.virtual_memory()
        total_mem_gb = round(mem_info.total / (1024 ** 3), 1)
        mem_pct = mem_info.percent

        disk = shutil.disk_usage(str(Path.home()))
        disk_free_gb = round(disk.free / (1024 ** 3), 1)

        temp = get_temperature(psutil_lib)
        fan = get_fan_rpm(psutil_lib)

        return {
            "CPU": f"{cpu_pct}%",
            "Memory": f"{mem_pct}% ({total_mem_gb}GB)",
            "Disk Free": f"{disk_free_gb} GB",
            "Temperature": str(temp),
            "Fan RPM": str(fan),
            "Time": time.strftime('%H:%M:%S')
        }
    except Exception as e:
        return {
            "CPU": "Error",
            "Memory": "Error",
            "Disk Free": "Error",
            "Temperature": "Error",
            "Fan RPM": "Error",
            "Time": time.strftime('%H:%M:%S')
        }


def get_temperature(psutil_lib=None):
    """Reads the system temperature from psutil."""
    if psutil_lib is None:
        psutil_lib = psutil
    if not hasattr(psutil_lib, 'sensors_temperatures'):
        return 'N/A'
    try:
        temps = psutil_lib.sensors_temperatures()
        if not temps:
            return 'N/A'
        for k, v in temps.items():
            if v and hasattr(v[0], 'current'):
                return f"{v[0].current}C"
    except Exception:
        pass
    return 'N/A'


def get_fan_rpm(psutil_lib=None):
    """Reads fan speeds from psutil."""
    if psutil_lib is None:
        psutil_lib = psutil
    if not hasattr(psutil_lib, 'sensors_fans'):
        return 'N/A'
    try:
        fans = psutil_lib.sensors_fans()
        if not fans:
            return 'N/A'
        for name, entries in fans.items():
            if entries and hasattr(entries[0], 'current'):
                return f"{entries[0].current} RPM"
    except Exception:
        pass
    return 'N/A'


def get_temperature_sensors(psutil_lib=None):
    """Returns list of (label, value) tuples for all temperature sensors."""
    if psutil_lib is None:
        psutil_lib = psutil
    if not hasattr(psutil_lib, 'sensors_temperatures'):
        return []
    try:
        temps = psutil_lib.sensors_temperatures()
        if not temps:
            return []
        sensors = []
        for name, entries in temps.items():
            for entry in entries:
                label = entry.label or name
                if hasattr(entry, 'current'):
                    sensors.append((label, f"{entry.current}C"))
        return sensors
    except Exception:
        return []


def get_fan_sensors(psutil_lib=None):
    """Returns list of (label, value) tuples for all fan sensors."""
    if psutil_lib is None:
        psutil_lib = psutil
    if not hasattr(psutil_lib, 'sensors_fans'):
        return []
    try:
        fans = psutil_lib.sensors_fans()
        if not fans:
            return []
        sensors = []
        for name, entries in fans.items():
            for entry in entries:
                label = entry.label or name
                value = f"{entry.current} RPM" if hasattr(entry, 'current') else 'N/A'
                sensors.append((label, value))
        return sensors
    except Exception:
        return []


def check_browser_installed():
    """Checks for common web browser installations."""
    if os.name == 'nt':
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        return any(Path(p).exists() for p in paths)
    else:
        import subprocess
        for name in ("google-chrome", "chrome", "chromium", "firefox"):
            try:
                res = subprocess.run(["which", name], capture_output=True)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
        return False


def detect_linux_distro():
    """Detects the Linux distribution name."""
    if os.name != 'posix' or not hasattr(__import__('platform'), 'system'):
        return None
    import platform
    if platform.system() != 'Linux':
        return None
    os_release = Path('/etc/os-release')
    if os_release.exists():
        try:
            data = os_release.read_text(encoding='utf-8')
            for line in data.splitlines():
                if line.startswith('ID='):
                    return line.split('=', 1)[1].strip().strip('"').lower()
        except Exception:
            pass
    return None
