# config_manager.py
import json
import os
import sys
from pathlib import Path

MARKER_FILE = Path.home() / ".novium_setup_done"
CONFIG_FILE = Path.cwd() / "config.json"
DEFAULT_CONFIG = {
    "logo_color": "BLUE",
    "hardware_monitoring": True,
    "web_search_enabled": True,
    "app_launcher_active": False,
    "autostart_enabled": False
}

SCRIPT_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = SCRIPT_DIR / "requirements.txt"


def load_config():
    """Loads configuration from disk, or returns default if not found."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with CONFIG_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    except Exception as e:
        print(f"Error loading config: {e}. Using default configuration.")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Saves the given configuration dictionary to disk."""
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving configuration: {e}")


def hard_reset():
    """Removes the marker and config files."""
    for path in (MARKER_FILE, CONFIG_FILE):
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
    remove_desktop_launcher()
    remove_autostart()
    return True


def pip_install_requirements(requirements_file=None, user=False):
    """Installs packages from requirements.txt."""
    if requirements_file is None:
        requirements_file = REQUIREMENTS_FILE
    if not requirements_file.exists():
        return False
    command = [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)]
    if user:
        command.append('--user')
    try:
        import subprocess
        subprocess.check_call(command)
        return True
    except Exception:
        return False


def ensure_dependencies():
    """Checks for psutil and auto-installs if missing."""
    import importlib
    try:
        import psutil
        return True
    except ImportError:
        pass

    print("Missing required dependency: psutil")
    if not REQUIREMENTS_FILE.exists():
        print("requirements.txt not found. Cannot auto-install dependencies.")
        return False

    print("Attempting automatic dependency installation...")
    if pip_install_requirements():
        try:
            importlib.import_module('psutil')
            print("Dependencies installed successfully.")
            return True
        except Exception:
            pass

    if os.name != 'nt':
        print("Retrying installation with --user flag...")
        if pip_install_requirements(user=True):
            try:
                importlib.import_module('psutil')
                print("Dependencies installed successfully.")
                return True
            except Exception:
                pass

    print("Automatic dependency installation failed. Run `python install.py` or `python -m pip install -r requirements.txt`.")
    return False


def get_windows_startup_folder():
    """Returns the Windows startup folder path."""
    appdata = os.getenv('APPDATA')
    if appdata:
        return Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    home = Path.home()
    fallback = home / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    return fallback


def create_desktop_launcher():
    """Creates a desktop shortcut/launcher for Novium."""
    home = Path.home()
    desktop = home / 'Desktop'
    if not desktop.exists():
        desktop = home
    launcher = desktop / ('run_novium.bat' if os.name == 'nt' else 'run_novium.sh')
    python_exe = sys.executable
    script = Path(__file__).resolve()
    try:
        if os.name == 'nt':
            content = f"@echo off\n\"{python_exe}\" \"{script}\"\n"
            launcher.write_text(content)
        else:
            content = f"#!{python_exe}\nimport os\nos.system(\"{python_exe} {script}\")\n"
            launcher.write_text(content)
            os.chmod(launcher, 0o755)
        print(f"Launcher created: {launcher}")
        return True
    except Exception as e:
        print(f"Failed to create launcher: {e}")
        return False


def remove_desktop_launcher():
    """Removes the desktop launcher file."""
    home = Path.home()
    desktop = home / 'Desktop'
    if not desktop.exists():
        desktop = home
    launcher = desktop / ('run_novium.bat' if os.name == 'nt' else 'run_novium.sh')
    try:
        if launcher.exists():
            launcher.unlink()
    except Exception:
        pass


def enable_autostart():
    """Enables Novium autostart on login."""
    if os.name == 'nt':
        startup = get_windows_startup_folder()
        target = startup / 'run_novium.bat'
        if not target.exists():
            create_desktop_launcher()
        try:
            launcher = Path.home() / 'Desktop' / 'run_novium.bat'
            if launcher.exists():
                import shutil
                shutil.copy(str(launcher), str(target))
                print(f"Autostart enabled: {target}")
                return True
        except Exception as e:
            print(f"Failed to enable autostart: {e}")
            return False
    else:
        autostart = Path.home() / '.config' / 'autostart'
        autostart.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart / 'novium.desktop'
        python_exe = sys.executable
        script = Path(__file__).resolve()
        content = f"[Desktop Entry]\nName=Novium\nExec={python_exe} {script}\nType=Application\n"
        try:
            desktop_file.write_text(content)
            print(f"Autostart enabled: {desktop_file}")
            return True
        except Exception as e:
            print(f"Failed to enable autostart: {e}")
            return False
    return False


def remove_autostart():
    """Removes Novium autostart entry."""
    if os.name == 'nt':
        startup = get_windows_startup_folder()
        target = startup / 'run_novium.bat'
        try:
            if target.exists():
                target.unlink()
        except Exception:
            pass
    else:
        autostart = Path.home() / '.config' / 'autostart'
        desktop_file = autostart / 'novium.desktop'
        try:
            if desktop_file.exists():
                desktop_file.unlink()
        except Exception:
            pass
