"""
config.py - Configuration management, versioning, dependencies, desktop integration
"""

import os
import sys
import json
import subprocess
import shutil
import platform
import urllib.request
import urllib.error
import zipfile
import io
import time
from pathlib import Path
from datetime import datetime

from utils import color_text, BOLD, GREEN, CYAN, YELLOW, RED

SCRIPT_DIR = Path(__file__).resolve().parent


def get_data_dir():
    """Get platform-specific data directory for Novium runtime files."""
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path.home() / '.config'
    data_dir = base / 'Novium'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DATA_DIR = get_data_dir()
CONFIG_FILE = DATA_DIR / "config.json"
VERSION_FILE = DATA_DIR / ".version"
MARKER_FILE = DATA_DIR / ".novium_setup_done"

DEFAULT_CONFIG = {
    "font": "default",
    "logo_color": "BLUE",
    "logo_mode": "novium",
    "hardware_monitoring": True,
    "web_search_enabled": True,
    "app_launcher_active": False,
    "autostart_enabled": False,
    "network": {
        "enabled": False,
        "server_url": "ws://localhost:8765",
        "client_id": None,
        "verified": False
    }
}


def load_config():
    # Migrate legacy config from repo dir to data dir (one-time)
    legacy = SCRIPT_DIR / "config.json"
    if legacy.exists() and not CONFIG_FILE.exists():
        try:
            shutil.copy2(str(legacy), str(CONFIG_FILE))
        except Exception:
            pass

    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        if "network" not in data:
            merged["network"] = DEFAULT_CONFIG["network"].copy()
        elif isinstance(data.get("network"), dict):
            merged["network"] = {**DEFAULT_CONFIG["network"], **data["network"]}
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False


def get_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "1.0.0"


def bump_version():
    try:
        parts = get_version().split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
            new_ver = ".".join(parts)
            VERSION_FILE.write_text(new_ver + "\n", encoding="utf-8")
            return new_ver
    except Exception:
        pass
    return None


_IMPORT_NAMES = {
    "websocket-client": "websocket",
}

def _import_pkg(name):
    mapped = _IMPORT_NAMES.get(name, name)
    mapped = mapped.replace("-", "_")
    try:
        __import__(mapped)
        return True
    except ImportError:
        return False

def ensure_dependencies():
    """Check all requirements from requirements.txt and auto-install any missing."""
    req_file = Path(__file__).resolve().parent / "requirements.txt"
    if not req_file.exists():
        return _import_pkg("psutil")

    missing = []
    with open(req_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg_name = line.split(">=")[0].split("==")[0].split("!=")[0].strip()
            if not _import_pkg(pkg_name):
                missing.append(pkg_name)

    if not missing:
        return True

    print(f"Missing {len(missing)} dependency/dependencies: {', '.join(missing)}")
    print("Installing...")
    for attempt_cmd in [
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        [sys.executable, "-m", "pip", "install", "--user", "-r", str(req_file)],
        [sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", str(req_file)],
    ]:
        try:
            r = subprocess.run(attempt_cmd, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                print("All dependencies installed successfully.")
                return True
        except Exception:
            continue

    print(f"Auto-install failed. Try: {sys.executable} -m pip install -r \"{req_file}\"")
    return False


# ── Desktop shortcuts & autostart ──

def create_desktop_launcher():
    system = platform.system()
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home()
    if system == "Windows":
        _create_windows_shortcut(desktop)
    else:
        _create_linux_desktop_file(desktop)
    print("Desktop shortcut created.")


def remove_desktop_launcher():
    system = platform.system()
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home()
    if system == "Windows":
        _remove_windows_shortcut(desktop)
    else:
        _remove_linux_desktop_file(desktop)
    print("Desktop shortcut removed.")


def enable_autostart():
    system = platform.system()
    if system == "Windows":
        _enable_windows_autostart()
    else:
        _enable_linux_autostart()
    print("Autostart enabled.")


def remove_autostart():
    system = platform.system()
    if system == "Windows":
        _remove_windows_autostart()
    else:
        _remove_linux_autostart()
    print("Autostart removed.")


def _create_windows_shortcut(target_dir):
    try:
        import winshell
        from win32com.client import Dispatch
        shortcut = target_dir / "Novium.lnk"
        shell = Dispatch("WScript.Shell")
        lnk = shell.CreateShortCut(str(shortcut))
        lnk.TargetPath = sys.executable
        lnk.Arguments = f'"{SCRIPT_DIR / "novium.py"}"'
        lnk.WorkingDirectory = str(SCRIPT_DIR)
        lnk.IconLocation = str(SCRIPT_DIR / "assets" / "novium.ico") + ", 0"
        lnk.Save()
    except ImportError:
        vbs_content = f'''Set WshShell = WScript.CreateObject("WScript.Shell")
Set lnk = WshShell.CreateShortcut("{target_dir / 'Novium.lnk'}")
lnk.TargetPath = "{sys.executable}"
lnk.Arguments = "{SCRIPT_DIR / 'novium.py'}"
lnk.WorkingDirectory = "{SCRIPT_DIR}"
lnk.Save()
'''
        vbs_path = SCRIPT_DIR / "_create_shortcut.vbs"
        vbs_path.write_text(vbs_content, encoding="utf-8")
        subprocess.run(["cscript", str(vbs_path)], capture_output=True, timeout=10)
        vbs_path.unlink(missing_ok=True)


def _remove_windows_shortcut(target_dir):
    for name in ["Novium.lnk", "run_novium.bat"]:
        p = target_dir / name
        p.unlink(missing_ok=True)


def _enable_windows_autostart():
    startup = Path(os.getenv("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup.mkdir(parents=True, exist_ok=True)
    bat_content = f'''@echo off
cd /d "{SCRIPT_DIR}"
start "" "{sys.executable}" "novium.py"
'''
    (startup / "run_novium.bat").write_text(bat_content, encoding="utf-8")


def _remove_windows_autostart():
    startup = Path(os.getenv("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    for name in ["run_novium.bat", "Novium.lnk"]:
        p = startup / name
        p.unlink(missing_ok=True)


def _create_linux_desktop_file(target_dir):
    desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Novium
Exec={sys.executable} {SCRIPT_DIR / 'novium.py'}
Icon={SCRIPT_DIR / 'assets' / 'novium-icon.svg'}
Terminal=true
Categories=Utility;
"""
    (target_dir / "Novium.desktop").write_text(desktop_entry, encoding="utf-8")
    (target_dir / "Novium.desktop").chmod(0o755)


def _remove_linux_desktop_file(target_dir):
    (target_dir / "Novium.desktop").unlink(missing_ok=True)


def _enable_linux_autostart():
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Novium
Exec={sys.executable} {SCRIPT_DIR / 'novium.py'}
Terminal=true
X-GNOME-Autostart-enabled=true
"""
    (autostart_dir / "novium.desktop").write_text(desktop_entry, encoding="utf-8")
    (autostart_dir / "novium.desktop").chmod(0o755)


def _remove_linux_autostart():
    autostart_dir = Path.home() / ".config" / "autostart"
    (autostart_dir / "novium.desktop").unlink(missing_ok=True)


# ── Fastfetch ──

def check_fastfetch_installed():
    try:
        r = subprocess.run(["fastfetch", "--version"], capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def install_fastfetch():
    system = platform.system()
    try:
        if system == "Linux":
            distro = _detect_distro()
            if distro in ("ubuntu", "debian"):
                subprocess.run(["sudo", "apt", "install", "-y", "fastfetch"], check=True, timeout=120)
            elif distro in ("fedora", "rhel", "centos"):
                subprocess.run(["sudo", "dnf", "install", "-y", "fastfetch"], check=True, timeout=120)
            elif distro in ("arch", "manjaro"):
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "fastfetch"], check=True, timeout=120)
            else:
                print("Unknown distro. Install fastfetch manually: https://github.com/fastfetch-cli/fastfetch")
        elif system == "Darwin":
            subprocess.run(["brew", "install", "fastfetch"], check=True, timeout=120)
        elif system == "Windows":
            subprocess.run(["winget", "install", "fastfetch"], check=True, timeout=120)
        print("fastfetch installed!")
    except Exception as e:
        print(f"Failed to install fastfetch: {e}")
        print("Install manually: https://github.com/fastfetch-cli/fastfetch")


def _detect_distro():
    os_release = Path("/etc/os-release")
    if os_release.exists():
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if line.startswith("ID="):
                return line.split("=", 1)[1].strip().strip('"').lower()
    return None


# ── Hard reset ──

def hard_reset():
    default = DEFAULT_CONFIG.copy()
    save_config(default)
    MARKER_FILE.unlink(missing_ok=True)
    print("Config reset to defaults.")
    print("Run Novium again for first-run setup.")


# ── Updates ──

GITHUB_API = "https://api.github.com/repos/novaozone187/Novium---Easy-Quick-Terminal/releases/latest"
GITHUB_REPO = "https://github.com/novaozone187/Novium---Easy-Quick-Terminal"


def check_for_updates():
    try:
        req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "Novium"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        latest = data.get("tag_name", "").lstrip("v")
        current = get_version()
        if latest and latest != current:
            return {"available": True, "current": current, "latest": latest, "url": data.get("html_url", GITHUB_REPO)}
        return {"available": False, "current": current, "latest": latest}
    except Exception:
        return {"available": False, "current": get_version(), "latest": None}


def apply_update(interactive=False):
    """Check for updates and auto-apply if available.

    Args:
        interactive: If True, prompt before overwriting.
    """
    info = check_for_updates()
    if not info.get("available"):
        if interactive:
            print(color_text("  Already up to date.", GREEN))
        return

    latest = info["latest"]
    current = info["current"]

    if interactive:
        print(color_text(f"  Update available: {current} → {latest}", CYAN))
        confirm = input(color_text("  Apply update now? (y/n): ", YELLOW)).strip().lower()
        if confirm != 'y':
            print(color_text("  Update cancelled.", YELLOW))
            return

    # ── Backup ──
    print(color_text("  Backing up current files...", CYAN))
    try:
        backup_dir = SCRIPT_DIR / ".novium_backup"
        if backup_dir.exists():
            shutil.rmtree(str(backup_dir))
        shutil.copytree(str(SCRIPT_DIR), str(backup_dir),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".novium_backup"))
        print(color_text("  Backup saved to .novium_backup", GREEN))
    except Exception as e:
        print(color_text(f"  Backup failed: {e}", RED))
        if interactive:
            return
        raise

    # ── Download ──
    try:
        print(color_text("  Downloading latest release...", CYAN))
        req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "Novium"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            release_data = json.loads(resp.read())

        zipball_url = release_data.get("zipball_url")
        if not zipball_url:
            print(color_text("  No download URL found.", RED))
            return

        req2 = urllib.request.Request(zipball_url, headers={"User-Agent": "Novium"})
        with urllib.request.urlopen(req2, timeout=60) as resp:
            zip_data = io.BytesIO(resp.read())

        print(color_text("  Extracting...", CYAN))
    except Exception as e:
        print(color_text(f"  Download failed: {e}", RED))
        print(color_text("  Your backup is at .novium_backup", YELLOW))
        return

    # ── Extract ──
    try:
        skip_files = {"config.json", ".version", "novium_network.log", "novium_tmp.txt"}
        files_copied = 0
        with zipfile.ZipFile(zip_data) as zf:
            # Find the novium/ subdirectory inside the zipball
            novium_prefix = None
            for name in zf.namelist():
                if name.endswith("/novium/") or name.endswith("/novium"):
                    novium_prefix = name
                    break
            if not novium_prefix:
                print(color_text("  Invalid update package: no novium/ directory found.", RED))
                return

            # Normalize prefix (ensure trailing /)
            if not novium_prefix.endswith("/"):
                novium_prefix += "/"

            for name in zf.namelist():
                if not name.startswith(novium_prefix):
                    continue
                rel = os.path.relpath(name, novium_prefix)
                if not rel or rel in skip_files or rel.startswith("__pycache__") or rel.startswith("."):
                    continue
                target = SCRIPT_DIR / rel
                if name.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                    files_copied += 1

        # Update .version
        tag = release_data.get("tag_name", "").lstrip("v")
        if tag:
            VERSION_FILE.write_text(tag + "\n", encoding="utf-8")

        print(color_text(f"  {files_copied} files updated. Version: {tag or latest}", GREEN))
    except Exception as e:
        print(color_text(f"  Extract/apply failed: {e}", RED))
        print(color_text("  Your backup is at .novium_backup", YELLOW))
        return

    # ── Restart ──
    print(color_text("  Update applied! Restarting...", BOLD + GREEN))
    time.sleep(1)
    _nrestart()


def _nrestart():
    """Restart Novium in-place (helper for update)."""
    sys.stdout.flush()
    script = os.path.abspath(sys.argv[0])
    if os.name == 'nt':
        subprocess.Popen(
            [sys.executable, script] + sys.argv[1:],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        time.sleep(1)
        try:
            os.kill(os.getppid(), 9)
        except Exception:
            pass
    else:
        os.execv(sys.executable, [sys.executable, script] + sys.argv[1:])
    os._exit(0)


# ── OS Setup ──

def run_os_setup():
    print("Running OS/System setup wizard...")
    system = platform.system()
    if system == "Windows":
        _run_windows_setup()
    elif system == "Linux":
        _run_linux_setup()
    elif system == "Darwin":
        _run_macos_setup()
    else:
        print(f"Unsupported OS: {system}")


def _run_windows_setup():
    print("Windows setup:")
    print("  1. Ensure Windows is up to date")
    print("  2. Install recommended tools:")
    tools = [
        ("Chrome", "https://www.google.com/chrome/"),
        ("VS Code", "https://code.visualstudio.com/"),
        ("Git", "https://git-scm.com/"),
        ("Node.js", "https://nodejs.org/"),
    ]
    for name, url in tools:
        print(f"     - {name}: {url}")
    print("  (Use 'install <name>' from Novium shell)")


def _run_linux_setup():
    print("Linux setup:")
    distro = _detect_distro()
    if distro in ("ubuntu", "debian"):
        print("  Run: sudo apt update && sudo apt upgrade -y")
        print("  Run: sudo apt install build-essential curl git -y")
    elif distro in ("fedora",):
        print("  Run: sudo dnf upgrade --refresh")
        print("  Run: sudo dnf groupinstall 'Development Tools'")
    elif distro in ("arch",):
        print("  Run: sudo pacman -Syu")
        print("  Run: sudo pacman -S base-devel git curl")
    else:
        print("  Update your system packages.")
    print("  Install fastfetch with: ff")


def _run_macos_setup():
    print("macOS setup:")
    print("  1. Install Xcode Command Line Tools: xcode-select --install")
    print("  2. Install Homebrew: https://brew.sh")
    print("  3. brew install git node")
