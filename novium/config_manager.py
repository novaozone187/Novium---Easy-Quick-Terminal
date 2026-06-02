# config_manager.py
import json
import os
import sys
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.error
import zipfile
from pathlib import Path

from utils import color_text, GREEN, YELLOW, RED

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
GITHUB_REPO = "novium"
GITHUB_BRANCH = "main"


def check_fastfetch_installed():
    """Checks if fastfetch is installed."""
    if os.name == 'nt':
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for d in path_dirs:
            exe = Path(d) / 'fastfetch.exe'
            if exe.exists():
                return True
        return False
    else:
        try:
            res = subprocess.run(['which', 'fastfetch'], capture_output=True)
            return res.returncode == 0
        except Exception:
            return False


def install_fastfetch():
    """Attempts to install fastfetch on the current platform."""
    if check_fastfetch_installed():
        return True

    if os.name == 'nt':
        for installer in ['winget', 'scoop', 'choco']:
            try:
                print(color_text(f"Trying to install fastfetch via {installer}...", YELLOW))
                result = subprocess.run(
                    [installer, 'install', 'fastfetch', '-y'],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                print(color_text(f"  {installer} output:", GREEN))
                if result.stdout:
                    for line in result.stdout.strip().splitlines():
                        print(f"    {line}")
                if check_fastfetch_installed():
                    print(color_text(f"fastfetch installed successfully via {installer}.", GREEN))
                    return True
            except subprocess.TimeoutExpired:
                print(color_text(f"  {installer} timed out.", RED))
            except FileNotFoundError:
                print(color_text(f"  {installer} not found on this system.", YELLOW))
            except Exception as e:
                print(color_text(f"  {installer} failed: {e}", RED))
                if hasattr(e, 'stderr') and e.stderr:
                    for line in e.stderr.strip().splitlines():
                        print(f"    {line}")
        print()
        print(color_text("All package managers failed. Install fastfetch manually:", RED))
        print(color_text("  winget install fastfetch", GREEN))
        print(color_text("  or download from: https://github.com/fastfetch-cli/fastfetch/releases", GREEN))
        return False
    elif os.name == 'posix':
        import platform
        if platform.system() == 'Darwin':
            try:
                subprocess.run(['brew', 'install', 'fastfetch'], check=True, capture_output=True)
                if check_fastfetch_installed():
                    return True
            except Exception:
                pass
        else:
            # Linux - try common package managers
            distro = detect_linux_distro()
            for pm in ['apt', 'dnf', 'pacman', 'zypper', 'apk']:
                try:
                    if pm == 'apt':
                        subprocess.run(['sudo', 'apt', 'install', '-y', 'fastfetch'], check=True, capture_output=True)
                    elif pm == 'dnf':
                        subprocess.run(['sudo', 'dnf', 'install', '-y', 'fastfetch'], check=True, capture_output=True)
                    elif pm == 'pacman':
                        subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'fastfetch'], check=True, capture_output=True)
                    elif pm == 'zypper':
                        subprocess.run(['sudo', 'zypper', 'install', '-y', 'fastfetch'], check=True, capture_output=True)
                    elif pm == 'apk':
                        subprocess.run(['sudo', 'apk', 'add', 'fastfetch'], check=True, capture_output=True)
                    if check_fastfetch_installed():
                        return True
                except Exception:
                    continue
            return False
    return False


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
    """Checks all dependencies and auto-installs any that are missing."""
    # Check Python packages from requirements.txt
    if REQUIREMENTS_FILE.exists():
        packages = []
        try:
            with REQUIREMENTS_FILE.open('r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        pkg = line.split('>')[0].split('=')[0].split('<')[0].split('~')[0].strip()
                        if pkg:
                            packages.append(pkg)
        except Exception:
            pass

        if packages:
            missing = []
            for pkg in packages:
                import_names = pkg.split('-')
                for name in import_names:
                    try:
                        __import__(name)
                        break
                    except ImportError:
                        continue
                else:
                    missing.append(pkg)

            if missing:
                print(color_text(f"Missing dependencies: {', '.join(missing)}. Installing...", YELLOW))
            else:
                print(f"Dependencies found: {', '.join(packages)}")

            if not pip_install_requirements():
                print(color_text("Automatic dependency installation failed. Run `python install.py` manually.", RED))
                return False

            # Verify all installed
            all_ok = True
            for pkg in packages:
                import_names = pkg.split('-')
                for name in import_names:
                    try:
                        __import__(name)
                        break
                    except ImportError:
                        all_ok = False
                        break
                if not all_ok:
                    if os.name != 'nt' and pip_install_requirements(user=True):
                        try:
                            __import__(name)
                            continue
                        except ImportError:
                            all_ok = False
                            break
            if all_ok:
                print(color_text("All dependencies installed successfully.", GREEN))

    # Check fastfetch (system binary)
    if not check_fastfetch_installed():
        print(color_text("fastfetch not found. Installing...", YELLOW))
        if install_fastfetch():
            print(color_text("fastfetch installed successfully.", GREEN))
        else:
            print(color_text("Failed to install fastfetch. Run `winget install fastfetch` manually.", RED))
    else:
        print(f"fastfetch: {color_text('OK', GREEN)}")

    return True


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
        # Windows: .bat file with proper window handling
        launcher = desktop / 'Novium.lnk' or desktop / 'run_novium.bat'
        bat_path = desktop / 'run_novium.bat'
        python_exe = sys.executable
        script = Path(__file__).resolve()
        try:
            content = f'@echo off\nchcp 65001 >nul\n"{python_exe}" "{script}"\necho.\necho Press any key to exit...\npause >nul\n'
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


def check_for_updates():
    """Checks GitHub for available updates. Returns (has_update, latest_commit, current_commit) or None on error."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/commits?sha={GITHUB_BRANCH}&per_page=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Novium/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            latest_commit = data[0]['sha'][:7]
        
        current_commit_file = SCRIPT_DIR / ".version"
        if current_commit_file.exists():
            current_commit = current_commit_file.read_text().strip()
            return latest_commit != current_commit, latest_commit, current_commit
        return True, latest_commit, "unknown"
    except Exception:
        return None, None, None


def backup_user_files():
    """Backs up user config and marker files."""
    backup_dir = SCRIPT_DIR / ".novium_backup"
    backup_dir.mkdir(exist_ok=True)
    
    if CONFIG_FILE.exists():
        shutil.copy2(str(CONFIG_FILE), str(backup_dir / "config.json"))
    if MARKER_FILE.exists():
        shutil.copy2(str(MARKER_FILE), str(backup_dir / ".novium_setup_done"))
    
    return backup_dir


def restore_user_files(backup_dir):
    """Restores user config and marker files from backup."""
    if (backup_dir / "config.json").exists():
        shutil.copy2(str(backup_dir / "config.json"), str(CONFIG_FILE))
    if (backup_dir / ".novium_setup_done").exists():
        shutil.copy2(str(backup_dir / ".novium_setup_done"), str(MARKER_FILE))


def apply_update():
    """Downloads and applies the latest update from GitHub."""
    print(color_text("Checking for updates...", YELLOW))
    has_update, latest_commit, current_commit = check_for_updates()
    
    if not has_update:
        print(color_text("Novium is already up to date.", GREEN))
        return False
    
    print(color_text(f"Update available! {current_commit} -> {latest_commit}", CYAN))
    confirm = input(color_text("Update now? (y/n): ", YELLOW)).strip().lower()
    if confirm != 'y':
        return False
    
    # Backup user files
    backup_dir = backup_user_files()
    print(color_text("Backed up user files.", GREEN))
    
    # Download latest version
    try:
        url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
        req = urllib.request.Request(url, headers={'User-Agent': 'Novium/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            zip_data = resp.read()
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "novium.zip"
            zip_path.write_bytes(zip_data)
            
            # Extract
            extract_dir = Path(temp_dir) / "novium-main"
            with zipfile.ZipFile(str(zip_path), 'r') as zf:
                zf.extractall(str(extract_dir))
            
            # Copy new files, preserving user files
            for item in extract_dir.iterdir():
                if item.name in ('.novium_backup', '.version'):
                    continue
                dest = SCRIPT_DIR / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(str(dest))
                    shutil.copytree(str(item), str(dest))
                else:
                    shutil.copy2(str(item), str(dest))
        
        # Save new version
        (SCRIPT_DIR / ".version").write_text(latest_commit)
        
        # Restore user files
        restore_user_files(backup_dir)
        
        print(color_text("Update applied successfully!", GREEN))
        return True
    except Exception as e:
        print(color_text(f"Update failed: {e}", RED))
        # Restore from backup
        restore_user_files(backup_dir)
        return False


def detect_os_info():
    """Detects OS and hardware information."""
    import platform
    os_info = {
        'os': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }
    
    # Try to get CPU info
    try:
        os_info['cpu'] = platform.processor() or 'Unknown'
    except Exception:
        os_info['cpu'] = 'Unknown'
    
    # Try to get RAM
    try:
        import psutil
        mem = psutil.virtual_memory()
        os_info['ram_gb'] = round(mem.total / (1024**3), 1)
    except Exception:
        os_info['ram_gb'] = 'Unknown'
    
    # Try to get GPU info
    try:
        import psutil
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            if temps:
                os_info['gpu_available'] = True
            else:
                os_info['gpu_available'] = False
        else:
            os_info['gpu_available'] = False
    except Exception:
        os_info['gpu_available'] = False
    
    return os_info


def get_driver_install_links(os_info):
    """Returns driver installation links based on OS and hardware."""
    links = []
    os = os_info.get('os', '').lower()
    
    if os == 'windows':
        links.append({
            'name': 'Windows Update',
            'url': 'https://updates.windows.com/',
            'desc': 'Critical system drivers and updates'
        })
        
        # GPU drivers
        try:
            import psutil
            temps = psutil.sensors_temperatures()
            if temps:
                for gpu_name in temps.keys():
                    if 'nvidia' in gpu_name.lower():
                        links.append({
                            'name': 'NVIDIA GeForce Experience',
                            'url': 'https://www.nvidia.com/Download/index.aspx',
                            'desc': 'NVIDIA GPU drivers'
                        })
                    elif 'amd' in gpu_name.lower():
                        links.append({
                            'name': 'AMD Adrenalin',
                            'url': 'https://www.amd.com/en/support',
                            'desc': 'AMD GPU drivers'
                        })
                    elif 'intel' in gpu_name.lower():
                        links.append({
                            'name': 'Intel Graphics Driver',
                            'url': 'https://www.intel.com/content/www/us/en/download-center/home.html',
                            'desc': 'Intel GPU drivers'
                        })
        except Exception:
            pass
        
        # Chipset drivers
        links.append({
            'name': 'Chipset Drivers',
            'url': 'https://www.intel.com/content/www/us/en/download-center/home.html',
            'desc': 'Intel chipset drivers (or visit your motherboard manufacturer)'
        })
    
    elif os == 'linux':
        links.append({
            'name': 'Update System',
            'url': 'https://docs.github.com/en/get-started/quickstart/set-up-git',
            'desc': f'Run: sudo apt update && sudo apt upgrade (Debian/Ubuntu)'
        })
        links.append({
            'name': 'Proprietary Drivers',
            'url': 'https://ubuntu.com/drivers',
            'desc': 'Ubuntu driver manager'
        })
    
    elif os == 'darwin':
        links.append({
            'name': 'macOS Software Update',
            'url': 'https://support.apple.com/en-us/102978',
            'desc': 'Check for macOS updates'
        })
    
    return links


def get_app_install_links(os_info):
    """Returns popular application installation links."""
    os = os_info.get('os', '').lower()
    links = []
    
    if os == 'windows':
        links.extend([
            {'name': 'Steam', 'url': 'https://store.steampowered.com/about/', 'desc': 'Game platform'},
            {'name': 'Discord', 'url': 'https://discord.com/download', 'desc': 'Communication'},
            {'name': 'VS Code', 'url': 'https://code.visualstudio.com/', 'desc': 'Code editor'},
            {'name': 'Firefox', 'url': 'https://www.mozilla.org/firefox/new/', 'desc': 'Web browser'},
            {'name': 'Chrome', 'url': 'https://www.google.com/chrome/', 'desc': 'Web browser'},
            {'name': 'Node.js', 'url': 'https://nodejs.org/', 'desc': 'JavaScript runtime'},
            {'name': 'Git', 'url': 'https://git-scm.com/downloads', 'desc': 'Version control'},
        ])
    elif os == 'linux':
        links.extend([
            {'name': 'Steam (Proton)', 'url': 'https://store.steampowered.com/about/', 'desc': 'Gaming on Linux'},
            {'name': 'Discord', 'url': 'https://discord.com/download', 'desc': 'Communication'},
            {'name': 'VS Code', 'url': 'https://code.visualstudio.com/', 'desc': 'Code editor'},
            {'name': 'Firefox', 'url': 'https://www.mozilla.org/firefox/new/', 'desc': 'Web browser'},
            {'name': 'Spotify', 'url': 'https://spotify.com/download', 'desc': 'Music streaming'},
        ])
    elif os == 'darwin':
        links.extend([
            {'name': 'Steam', 'url': 'https://store.steampowered.com/about/', 'desc': 'Game platform'},
            {'name': 'Discord', 'url': 'https://discord.com/download', 'desc': 'Communication'},
            {'name': 'VS Code', 'url': 'https://code.visualstudio.com/', 'desc': 'Code editor'},
            {'name': 'Chrome', 'url': 'https://www.google.com/chrome/', 'desc': 'Web browser'},
            {'name': 'Homebrew', 'url': 'https://brew.sh/', 'desc': 'Package manager'},
        ])
    
    return links


def run_os_setup():
    """Runs the OS/System setup wizard."""
    import webbrowser
    clear()
    print(color_text("=== OS / SYSTEM SETUP WIZARD ===", BOLD + CYAN))
    print()
    
    # Detect system info
    os_info = detect_os_info()
    print(color_text("--- System Information ---", BOLD + CYAN))
    print(f"  OS: {os_info['os']} {os_info['release']}")
    print(f"  Machine: {os_info['machine']}")
    print(f"  CPU: {os_info['cpu']}")
    print(f"  RAM: {os_info.get('ram_gb', 'Unknown')} GB")
    print()
    
    # Driver recommendations
    driver_links = get_driver_install_links(os_info)
    if driver_links:
        print(color_text("--- Recommended Drivers ---", BOLD + CYAN))
        for i, link in enumerate(driver_links, 1):
            print(color_text(f"  {i}) {link['name']}", GREEN))
            print(f"     {link['desc']}")
            print(f"     {link['url']}")
            print()
        
        choice = input(color_text("Select driver to open (number), or skip: ", YELLOW)).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(driver_links):
            link = driver_links[int(choice) - 1]
            print(color_text(f"Opening {link['name']}...", CYAN))
            webbrowser.open(link['url'])
    
    print()
    
    # App recommendations with tick-off checklist
    app_links = get_app_install_links(os_info)
    if app_links:
        print(color_text("--- Popular Applications ---", BOLD + CYAN))
        print(color_text("Tick off apps you want to install (enter comma-separated numbers, e.g., 1,3,5):", BLUE))
        print()
        for i, link in enumerate(app_links, 1):
            print(color_text(f"  [{i}] {link['name']}", GREEN))
            print(f"      {link['desc']}")
            print(f"      {link['url']}")
            print()
        
        choice = input(color_text("Select apps to install (comma-separated numbers, or skip): ", YELLOW)).strip()
        if choice:
            selected = [int(x.strip()) for x in choice.split(',') if x.strip().isdigit()]
            for num in selected:
                if 1 <= num <= len(app_links):
                    link = app_links[num - 1]
                    print(color_text(f"Opening {link['name']} installer...", CYAN))
                    webbrowser.open(link['url'])
    
    print()
    input(color_text("Press Enter to continue...", BLUE))
