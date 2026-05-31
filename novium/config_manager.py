# config_manager.py
import json
import os
import sys
from pathlib import Path

MARKER_FILE = Path.home() / ".novium_setup_done"
CONFIG_FILE = Path.cwd() / "config.json"
DEFAULT_CONFIG = {
    "logo_color": "BLUE",
    "logo_mode": "novium",
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
    """Checks all dependencies on every startup and auto-installs any that are missing."""
    if not REQUIREMENTS_FILE.exists():
        print("requirements.txt not found. Skipping dependency check.")
        return True

    # Parse requirements file for package names
    packages = []
    try:
        with REQUIREMENTS_FILE.open('r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Strip version specifiers (>=, ==, <=, ~=, !=)
                    pkg = line.split('>')[0].split('=')[0].split('<')[0].split('~')[0].strip()
                    if pkg:
                        packages.append(pkg)
    except Exception:
        pass

    if not packages:
        return True

    missing = []
    for pkg in packages:
        # Try common import names
        import_names = pkg.split('-')
        for name in import_names:
            try:
                __import__(name)
                break
            except ImportError:
                continue
        else:
            missing.append(pkg)

    if not missing:
        return True

    print(f"Auto-installing missing dependencies: {', '.join(missing)}")
    if pip_install_requirements():
        # Verify all installed
        for pkg in missing:
            import_names = pkg.split('-')
            for name in import_names:
                try:
                    __import__(name)
                    break
                except ImportError:
                    continue
            else:
                # Retry with --user on non-Windows
                if os.name != 'nt' and pip_install_requirements(user=True):
                    try:
                        __import__(name)
                        continue
                    except ImportError:
                        pass
                print(f"Warning: Failed to install {pkg}")
        print(color_text("All dependencies installed successfully.", GREEN))
        return True

    print(color_text("Automatic dependency installation failed. Run `python install.py`.", RED))
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

    if os.name == 'nt':
        # Windows: .bat file
        launcher = desktop / 'Novium.lnk' or desktop / 'run_novium.bat'
        bat_path = desktop / 'run_novium.bat'
        python_exe = sys.executable
        script = Path(__file__).resolve()
        try:
            content = f'@echo off\nchcp 65001 >nul\n"{python_exe}" "{script}"\npause\n'
            bat_path.write_text(content)
            # Try to create a .lnk using PowerShell
            try:
                import subprocess
                ps_command = (
                    f'$WshShell = New-Object -ComObject WScript.Shell; '
                    f'$Shortcut = $WshShell.CreateShortcut("{bat_path.parent / 'Novium.lnk'}"); '
                    f'$Shortcut.TargetPath = "{python_exe}"; '
                    f'$Shortcut.Arguments = "{script}"; '
                    f'$Shortcut.WorkingDirectory = "{bat_path.parent}"; '
                    f'$Shortcut.IconLocation = "shell32.dll,13"; '
                    f'$Shortcut.Save()'
                )
                subprocess.run(['powershell', '-Command', ps_command], check=True, capture_output=True)
                print(f"Desktop shortcut created: {bat_path.parent / 'Novium.lnk'}")
            except Exception:
                pass
            print(f"Launcher created: {bat_path}")
            return True
        except Exception as e:
            print(f"Failed to create launcher: {e}")
            return False
    else:
        # Linux/macOS: create a .desktop file that opens a terminal
        python_exe = sys.executable
        script = Path(__file__).resolve()
        icon_path = desktop / 'novium-icon.svg'

        # Create a simple icon
        try:
            icon_svg = r'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="20" fill="#1a1a2e"/>
  <rect x="8" y="8" width="112" height="112" rx="16" fill="#16213e"/>
  <text x="64" y="82" text-anchor="middle" font-family="monospace" font-size="48" font-weight="bold" fill="#00d4ff">N</text>
</svg>'''
            icon_path.write_text(icon_svg, encoding='utf-8')
        except Exception:
            icon_path = None

        # Create .desktop launcher
        desktop_file = desktop / 'Novium.desktop'
        content = (
            f'[Desktop Entry]\n'
            f'Name=Novium\n'
            f'Comment=Terminal-based app launcher and system dashboard\n'
            f'Exec={python_exe} {script}\n'
            f'Icon={icon_path}\n'
            f'Terminal=true\n'
            f'Type=Application\n'
            f'Categories=System;Utility;\n'
        )
        try:
            desktop_file.write_text(content, encoding='utf-8')
            print(f"Desktop launcher created: {desktop_file}")
            print(f"Double-click it to launch Novium in a terminal.")
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

    if os.name == 'nt':
        for name in ('Novium.lnk', 'run_novium.bat'):
            try:
                target = desktop / name
                if target.exists():
                    target.unlink()
            except Exception:
                pass
    else:
        # Linux/macOS: remove .desktop file and icon
        for name in ('Novium.desktop', 'novium-icon.svg'):
            try:
                target = desktop / name
                if target.exists():
                    target.unlink()
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
        # Create icon for autostart
        icon_path = autostart / 'novium-icon.svg'
        try:
            icon_svg = r'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="20" fill="#1a1a2e"/>
  <rect x="8" y="8" width="112" height="112" rx="16" fill="#16213e"/>
  <text x="64" y="82" text-anchor="middle" font-family="monospace" font-size="48" font-weight="bold" fill="#00d4ff">N</text>
</svg>'''
            icon_path.write_text(icon_svg, encoding='utf-8')
        except Exception:
            icon_path = None

        icon_line = f'Icon={icon_path}\n' if icon_path.exists() else ''
        content = (
            f'[Desktop Entry]\n'
            f'Name=Novium\n'
            f'Comment=Terminal-based app launcher and system dashboard\n'
            f'Exec={python_exe} {script}\n'
            f'Terminal=true\n'
            f'Type=Application\n'
            f'Categories=System;Utility;\n'
            f'{icon_line}'
        )
        try:
            desktop_file.write_text(content, encoding='utf-8')
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


def nuke_novium():
    """Completely removes Novium from the system."""
    import shutil
    removed = []
    failed = []

    # 1. Remove marker file
    if MARKER_FILE.exists():
        try:
            MARKER_FILE.unlink()
            removed.append("Setup marker file")
        except Exception:
            failed.append("Setup marker file")

    # 2. Remove config.json
    if CONFIG_FILE.exists():
        try:
            CONFIG_FILE.unlink()
            removed.append("config.json")
        except Exception:
            failed.append("config.json")

    # 3. Remove desktop launcher
    remove_desktop_launcher()
    removed.append("Desktop launcher")

    # 4. Remove autostart entry
    remove_autostart()
    removed.append("Autostart entry")

    # 5. Uninstall psutil
    try:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', 'psutil'])
        removed.append("psutil (pip)")
    except Exception:
        pass

    return removed, failed
