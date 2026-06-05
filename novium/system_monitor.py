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


def run_performance_check():
    """Run system performance checks.

    Returns list of dicts: {check, status, message, fix, fix_cmd}
    status is one of "OK", "WARNING", "FAIL"
    fix is a human-readable fix description (empty string if no auto-fix available)
    fix_cmd is a list of command strings to run (empty list if no auto-fix)
    """
    import subprocess as _sp

    results = []

    # ── 1. Power Plan (Windows only) ──
    if os.name == 'nt':
        try:
            r = _sp.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=5)
            out = r.stdout.strip()
            if "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in out:
                results.append({"check": "Power Plan", "status": "OK", "message": "High Performance active", "fix": "", "fix_cmd": []})
            elif "e9a42b02-d5df-448d-aa00-03f14749eb61" in out:
                results.append({"check": "Power Plan", "status": "OK", "message": "Ultimate Performance active", "fix": "", "fix_cmd": []})
            else:
                name = out.split(")", 1)[-1].strip() if ")" in out else out
                results.append({"check": "Power Plan", "status": "WARNING", "message": f"'{name}' may limit performance", "fix": "Switch to High Performance", "fix_cmd": ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"]})
        except Exception as e:
            results.append({"check": "Power Plan", "status": "WARNING", "message": f"Could not check: {e}", "fix": "", "fix_cmd": []})
    else:
        results.append({"check": "Power Plan", "status": "OK", "message": "Linux — check cpufreq governor manually", "fix": "", "fix_cmd": []})

    # ── 2. GPU Driver ──
    if os.name == 'nt':
        try:
            r = _sp.run(["wmic", "path", "win32_videocontroller", "get", "name,DriverVersion", "/format:csv"],
                        capture_output=True, text=True, timeout=5)
            lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and "Node" not in l]
            gpu_found = False
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 3:
                    gpu_name = parts[-2].strip()
                    driver_ver = parts[-1].strip()
                    if gpu_name and driver_ver:
                        gpu_found = True
                        results.append({"check": "GPU Driver", "status": "OK", "message": f"{gpu_name} — {driver_ver}", "fix": "", "fix_cmd": []})
            if not gpu_found:
                results.append({"check": "GPU Driver", "status": "WARNING", "message": "Could not determine GPU driver", "fix": "Run dxdiag to check manually", "fix_cmd": ["dxdiag", "/t"]})
        except Exception as e:
            results.append({"check": "GPU Driver", "status": "WARNING", "message": f"Check failed: {e}", "fix": "", "fix_cmd": []})
    else:
        try:
            r = _sp.run(["lspci", "-v"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                if "VGA" in line or "3D" in line or "Display" in line:
                    results.append({"check": "GPU", "status": "OK", "message": line.strip(), "fix": "", "fix_cmd": []})
                    break
            else:
                results.append({"check": "GPU", "status": "WARNING", "message": "No GPU info found", "fix": "Install lspci (pciutils)", "fix_cmd": ["sudo", "apt", "install", "-y", "pciutils"]})
        except Exception:
            results.append({"check": "GPU", "status": "WARNING", "message": "Could not check (lspci not found)", "fix": "Install lspci (pciutils)", "fix_cmd": ["sudo", "apt", "install", "-y", "pciutils"]})

    # ── 3. Pending Reboot ──
    if os.name == 'nt':
        reboot_pending = False
        try:
            r = _sp.run(["reg", "query", r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager",
                         "/v", "PendingFileRenameOperations"], capture_output=True, text=True, timeout=5)
            if "PendingFileRenameOperations" in r.stdout:
                reboot_pending = True
        except Exception:
            pass
        if not reboot_pending:
            try:
                r = _sp.run(["reg", "query", r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update",
                             "/v", "RebootRequired"], capture_output=True, text=True, timeout=5)
                if "RebootRequired" in r.stdout:
                    reboot_pending = True
            except Exception:
                pass
        if reboot_pending:
            results.append({"check": "Pending Reboot", "status": "WARNING", "message": "Reboot required", "fix": "Restart now", "fix_cmd": ["shutdown", "/r", "/t", "0"]})
        else:
            results.append({"check": "Pending Reboot", "status": "OK", "message": "No reboot needed", "fix": "", "fix_cmd": []})
    else:
        reboot_pending = os.path.exists("/var/run/reboot-required")
        if reboot_pending:
            results.append({"check": "Pending Reboot", "status": "WARNING", "message": "Reboot required", "fix": "Restart now", "fix_cmd": ["sudo", "reboot"]})
        else:
            results.append({"check": "Pending Reboot", "status": "OK", "message": "No reboot needed", "fix": "", "fix_cmd": []})

    # ── 4. Disk Health ──
    if os.name == 'nt':
        try:
            r = _sp.run(["wmic", "diskdrive", "get", "status"], capture_output=True, text=True, timeout=5)
            statuses = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().lower() in ("ok", "bad", "warning", "unknown")]
            bad = [s for s in statuses if s.lower() != "ok"]
            if bad:
                results.append({"check": "Disk Health", "status": "FAIL", "message": f"{len(bad)} drive(s) report: {', '.join(bad)}", "fix": "Back up data immediately", "fix_cmd": []})
            elif statuses:
                results.append({"check": "Disk Health", "status": "OK", "message": f"{len(statuses)} drive(s): all OK", "fix": "", "fix_cmd": []})
            else:
                results.append({"check": "Disk Health", "status": "WARNING", "message": "Could not read disk status", "fix": "", "fix_cmd": []})
        except Exception as e:
            results.append({"check": "Disk Health", "status": "WARNING", "message": f"Check failed: {e}", "fix": "", "fix_cmd": []})
    else:
        try:
            r = _sp.run(["smartctl", "--scan"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                results.append({"check": "Disk Health", "status": "OK", "message": "smartctl available", "fix": "", "fix_cmd": []})
            else:
                results.append({"check": "Disk Health", "status": "WARNING", "message": "smartctl not available", "fix": "Install smartmontools", "fix_cmd": ["sudo", "apt", "install", "-y", "smartmontools"]})
        except Exception:
            results.append({"check": "Disk Health", "status": "WARNING", "message": "smartctl not found", "fix": "Install smartmontools", "fix_cmd": ["sudo", "apt", "install", "-y", "smartmontools"]})

    # ── 5. Memory ──
    try:
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / (1024 ** 3), 1)
        avail_gb = round(mem.available / (1024 ** 3), 1)
        pct = mem.percent
        if pct > 90:
            results.append({"check": "Memory", "status": "FAIL", "message": f"{total_gb}GB — {pct}% used ({avail_gb}GB free)", "fix": "Close unused apps or add RAM", "fix_cmd": []})
        elif pct > 75:
            results.append({"check": "Memory", "status": "WARNING", "message": f"{total_gb}GB — {pct}% used ({avail_gb}GB free)", "fix": "Close background apps", "fix_cmd": []})
        else:
            results.append({"check": "Memory", "status": "OK", "message": f"{total_gb}GB — {pct}% used ({avail_gb}GB free)", "fix": "", "fix_cmd": []})
    except Exception as e:
        results.append({"check": "Memory", "status": "WARNING", "message": f"Check failed: {e}", "fix": "", "fix_cmd": []})

    # ── 6. Disk Space ──
    try:
        if os.name == 'nt':
            usage = shutil.disk_usage("C:\\")
        else:
            usage = shutil.disk_usage("/")
        total_gb = round(usage.total / (1024 ** 3), 1)
        free_gb = round(usage.free / (1024 ** 3), 1)
        free_pct = round(usage.free / usage.total * 100, 1)
        if free_pct < 5:
            results.append({"check": "Disk Space", "status": "FAIL", "message": f"{free_gb}GB free / {total_gb}GB ({free_pct}%)", "fix": "Run Disk Cleanup", "fix_cmd": ["cleanmgr"] if os.name == 'nt' else []})
        elif free_pct < 15:
            results.append({"check": "Disk Space", "status": "WARNING", "message": f"{free_gb}GB free / {total_gb}GB ({free_pct}%)", "fix": "Run Disk Cleanup", "fix_cmd": ["cleanmgr"] if os.name == 'nt' else []})
        else:
            results.append({"check": "Disk Space", "status": "OK", "message": f"{free_gb}GB free / {total_gb}GB ({free_pct}%)", "fix": "", "fix_cmd": []})
    except Exception as e:
        results.append({"check": "Disk Space", "status": "WARNING", "message": f"Check failed: {e}", "fix": "", "fix_cmd": []})

    # ── 7. Startup Programs (Windows) ──
    if os.name == 'nt':
        try:
            r = _sp.run(["wmic", "startup", "get", "caption"], capture_output=True, text=True, timeout=5)
            items = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().lower() != "caption"]
            if len(items) > 15:
                results.append({"check": "Startup Programs", "status": "WARNING", "message": f"{len(items)} startup items", "fix": "Disable unused in Task Manager > Startup", "fix_cmd": []})
            elif len(items) > 8:
                results.append({"check": "Startup Programs", "status": "OK", "message": f"{len(items)} startup items (moderate)", "fix": "", "fix_cmd": []})
            else:
                results.append({"check": "Startup Programs", "status": "OK", "message": f"{len(items)} startup items", "fix": "", "fix_cmd": []})
        except Exception:
            results.append({"check": "Startup Programs", "status": "WARNING", "message": "Could not enumerate", "fix": "", "fix_cmd": []})

    # ── 8. CPU ──
    try:
        cpu_count = psutil.cpu_count(logical=True)
        cpu_phys = psutil.cpu_count(logical=False) or "?"
        cpu_freq = psutil.cpu_freq()
        freq_str = f"{round(cpu_freq.current)}MHz" if cpu_freq else "N/A"
        results.append({"check": "CPU", "status": "OK", "message": f"{cpu_phys}C/{cpu_count}T @ {freq_str}", "fix": "", "fix_cmd": []})
    except Exception as e:
        results.append({"check": "CPU", "status": "WARNING", "message": f"Check failed: {e}", "fix": "", "fix_cmd": []})

    return results


def run_security_check():
    """Run basic security/suspicious activity checks.

    Returns list of dicts: {check, status, message}
    """
    import subprocess as _sp

    results = []

    if os.name == 'nt':
        # ── 1. Windows Defender status ──
        try:
            r = _sp.run(["sc", "query", "WinDefend"], capture_output=True, text=True, timeout=5)
            if "RUNNING" in r.stdout or "STATE" in r.stdout and "4" in r.stdout:
                results.append({"check": "Windows Defender", "status": "OK", "message": "Running"})
            elif "STOPPED" in r.stdout:
                results.append({"check": "Windows Defender", "status": "FAIL", "message": "STOPPED — malware risk"})
            else:
                results.append({"check": "Windows Defender", "status": "WARNING", "message": "Status unknown"})
        except Exception:
            results.append({"check": "Windows Defender", "status": "WARNING", "message": "Could not check"})

        # ── 2. Firewall status ──
        try:
            r = _sp.run(["netsh", "advfirewall", "show", "allprofiles", "state"], capture_output=True, text=True, timeout=5)
            on_count = sum(1 for line in r.stdout.splitlines() if "ON" in line)
            if on_count >= 3:
                results.append({"check": "Firewall", "status": "OK", "message": "Enabled (all profiles)"})
            elif on_count > 0:
                results.append({"check": "Firewall", "status": "WARNING", "message": f"Enabled on {on_count}/3 profiles"})
            else:
                results.append({"check": "Firewall", "status": "FAIL", "message": "Disabled — security risk"})
        except Exception:
            results.append({"check": "Firewall", "status": "WARNING", "message": "Could not check"})

        # ── 3. UAC status ──
        try:
            r = _sp.run(["reg", "query", r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                         "/v", "EnableLUA"], capture_output=True, text=True, timeout=5)
            if "0x1" in r.stdout:
                results.append({"check": "UAC", "status": "OK", "message": "Enabled"})
            elif "0x0" in r.stdout:
                results.append({"check": "UAC", "status": "FAIL", "message": "Disabled — admin rights unchecked"})
            else:
                results.append({"check": "UAC", "status": "WARNING", "message": "Status unknown"})
        except Exception:
            results.append({"check": "UAC", "status": "WARNING", "message": "Could not check"})

    # ── 4. Suspicious processes ──
    suspicious_names = ["powershell.exe", "cmd.exe", "wscript.exe", "cscript.exe", "mshta.exe", "regsvr32.exe"]
    suspicious_in_temp = []
    high_cpu_procs = []
    try:
        for proc in psutil.process_iter(["pid", "name", "exe", "cpu_percent"]):
            try:
                name = proc.info.get("name", "").lower()
                exe = proc.info.get("exe", "") or ""
                cpu = proc.info.get("cpu_percent") or 0
                if name in suspicious_names and ("temp" in exe.lower() or "appdata\\local\\temp" in exe.lower()):
                    suspicious_in_temp.append(name)
                if cpu > 50:
                    high_cpu_procs.append((name, cpu))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if suspicious_in_temp:
            results.append({"check": "Suspicious Processes", "status": "FAIL", "message": f"Scripts from temp: {', '.join(set(suspicious_in_temp))}"})
        elif high_cpu_procs:
            worst = max(high_cpu_procs, key=lambda x: x[1])
            results.append({"check": "Suspicious Processes", "status": "WARNING", "message": f"High CPU: {worst[0]} ({worst[1]:.0f}%)"})
        else:
            results.append({"check": "Suspicious Processes", "status": "OK", "message": "No anomalies"})
    except Exception:
        results.append({"check": "Suspicious Processes", "status": "WARNING", "message": "Could not scan"})

    # ── 5. Network connections ──
    try:
        conns = psutil.net_connections()
        est = [c for c in conns if c.status == "ESTABLISHED"]
        listening = [c for c in conns if c.status == "LISTEN"]
        unknown_ports = [str(c.laddr.port) for c in listening if c.laddr.port > 49151 and c.pid and c.pid > 0]
        msg = f"{len(est)} established, {len(listening)} listening"
        if unknown_ports:
            msg += f", {len(unknown_ports)} high-port listeners"
            results.append({"check": "Network", "status": "WARNING", "message": msg})
        else:
            results.append({"check": "Network", "status": "OK", "message": msg})
    except Exception:
        results.append({"check": "Network", "status": "WARNING", "message": "Could not scan"})

    # ── 6. Auto-start entries ──
    if os.name == 'nt':
        try:
            r = _sp.run(["wmic", "startup", "get", "caption"], capture_output=True, text=True, timeout=5)
            items = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().lower() != "caption"]
            if len(items) > 20:
                results.append({"check": "Startup Entries", "status": "WARNING", "message": f"{len(items)} items — review in Task Manager"})
            else:
                results.append({"check": "Startup Entries", "status": "OK", "message": f"{len(items)} items"})
        except Exception:
            results.append({"check": "Startup Entries", "status": "WARNING", "message": "Could not check"})
    else:
        results.append({"check": "Startup Entries", "status": "OK", "message": "Not checked on Linux"})

    return results
