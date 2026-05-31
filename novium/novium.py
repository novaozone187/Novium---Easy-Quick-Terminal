# novium.py - Main application logic for Novium
# Clean, modular, no duplication

import os
import sys
import time
import subprocess
import platform
from pathlib import Path

# Local imports
from utils import (
    color_text, BOLD, BLUE, CYAN, GREEN, YELLOW, RED, MAGENTA, RESET,
    clear, set_windows_ansi
)
from config_manager import (
    load_config, save_config, ensure_dependencies, MARKER_FILE,
    create_desktop_launcher, enable_autostart, remove_autostart,
    hard_reset, remove_desktop_launcher
)
from system_monitor import (
    get_system_stats_snapshot, get_temperature, get_fan_rpm,
    get_temperature_sensors, get_fan_sensors, check_browser_installed,
    detect_linux_distro
)
from ui import (
    display_logo, render_shell,
    render_sensor_screen, render_settings_screen, render_setup_screen
)

# --- Constants ---

FULL_LOGO = r"""
.-----------------. .----------------.  .----------------.  .----------------.  .----------------.  .----------------.
| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
| | ____  _____  | || |     ____     | || | ____   ____  | || |     _____    | || | _____  _____ | || | ____    ____ | |
| ||_   \|_   _| | || |   .'    `.   | || ||_  _| |_  _| | || |    |_   _|   | || ||_   _||_   _|| || ||_   \  /   _|| |
| |  |   \ | |   | || |  /  .--.  \  | || |  \ \   / /   | || |      | |     | || |  | |    | |  | || |  |   \/   |  | |
| |  | |\ \| |   | || |  | |    | |  | || |   \ \ / /    | || |      | |     | || |  | '    ' |  | || |  | |\  /| |  | |
| | _| |_\   |_  | || |  \  `--'  /  | || |    \ ' /     | || |     _| |_    | || |   \ `--' /   | || | _| |_\/_| |_ | |
| ||_____|\____| | || |   `.____.'   | || |     \_/      | || |    |_____|   | || |    `.__.'    | || ||_____||_____|| |
| |              | || |              | || |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
  '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------'
"""

N_LOGO = r"""
.-----------------.
| .--------------. |
| | ____  _____  | |
| ||_   \|_   _| | |
| |  |   \ | |   | |
| |  | |\ \| |   | |
| | _| |_\   |_  | |
| ||_____|\____| | |
| |              | |
| '--------------' |
'----------------'
"""

GENERAL_COMMANDS = ['help', 'stats', 'fan', 'settings', 'setup', 'sysinfo', 'nhome', 'clear', 'exit']

OS_COMMAND_HINTS = {
    'nt': ['dir', 'cls', 'ipconfig', 'tasklist', 'systeminfo'],
    'posix': ['ls', 'clear', 'uname -a', 'top', 'df -h']
}


# --- Splash & Detection ---

def splash_screen():
    """Displays the animated splash screen."""
    set_windows_ansi()
    clear()
    display_logo(FULL_LOGO, delay=0.002)
    print()
    print(color_text('Welcome to Novium', CYAN))
    for seconds in range(3, 0, -1):
        countdown = color_text(f'Starting in {seconds}...', YELLOW)
        print(countdown, end='\r', flush=True)
        time.sleep(1)
    cols = __import__('shutil').get_terminal_size().columns
    print(' ' * cols, end='\r')
    time.sleep(0.2)


def run_system_detection():
    """Runs environment detection and displays results."""
    set_windows_ansi()
    detected = {}
    detected['Web Browser'] = check_browser_installed()
    detected['psutil'] = True
    detected['python'] = sys.version.split()[0]
    detected['platform'] = platform.platform()
    detected['fastfetch'] = check_fastfetch_installed()

    print()
    print(color_text("--- System Detection ---", BOLD + CYAN))
    for name, value in detected.items():
        icon = 'OK' if value else 'MISSING'
        color = GREEN if value else RED
        print(f"  {name}: {color_text(icon, color)}")
    print()

    if not detected['psutil']:
        print(color_text("psutil is required. Please run: pip install psutil", RED))
        input("Press Enter to exit...")
        sys.exit(1)

    input(color_text("Press Enter to continue...", BLUE))
    return detected


# --- Shell Commands ---

def show_shell_help():
    """Shows built-in command help."""
    clear()
    print(color_text('Novium built-in commands:', BOLD + CYAN))
    print(color_text('  help    - show this help text', BLUE))
    print(color_text('  stats   - display current system stats', BLUE))
    print(color_text('  fan     - show fan and temperature sensor status', BLUE))
    print(color_text('  settings- open Novium settings', BLUE))
    print(color_text('  setup   - rerun first-run setup options', BLUE))
    print(color_text('  sysinfo - display detailed system information', BLUE))
    print(color_text('  nhome   - return to the Novium home shell screen', BLUE))
    print(color_text('  clear   - clear the screen', BLUE))
    print(color_text('  exit    - quit Novium', BLUE))
    print()
    input(color_text('Press Enter to continue...', CYAN))


def show_stats():
    """Displays current system stats."""
    clear()
    stats = get_system_stats_snapshot()
    print(color_text("=== SYSTEM STATS ===", BOLD + CYAN))
    print()
    for key, value in stats.items():
        print(f"  {key:<15}: {color_text(value, GREEN)}")
    print()
    input(color_text("Press Enter to continue...", BLUE))


def show_sysinfo():
    """Displays detailed system information."""
    clear()
    stats = get_system_stats_snapshot()
    print(color_text("=== SYSTEM INFORMATION ===", BOLD + CYAN))
    print()
    print(f"  OS:           {platform.system()} {platform.release()}")
    print(f"  Platform:     {platform.platform()}")
    print(f"  Python:       {sys.version.split()[0]}")
    print(f"  CPU cores:    {__import__('os').cpu_count()}")
    print(f"  Memory:       {stats.get('Memory', 'N/A')}")
    print(f"  Disk Free:    {stats.get('Disk Free', 'N/A')}")
    print(f"  Temperature:  {stats.get('Temperature', 'N/A')}")
    print(f"  Fan RPM:      {stats.get('Fan RPM', 'N/A')}")
    print()
    input(color_text("Press Enter to continue...", BLUE))


def execute_command(cmd):
    """Executes a system command and returns output lines."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30
        )
        output = []
        if result.stdout:
            output.extend(result.stdout.strip().splitlines())
        if result.stderr:
            output.extend([color_text(line, YELLOW) for line in result.stderr.strip().splitlines()])
        return output if output else [color_text("Command executed successfully.", GREEN)]
    except subprocess.TimeoutExpired:
        return [color_text("Command timed out.", RED)]
    except Exception as e:
        return [color_text(f"Error: {e}", RED)]


def web_search(query):
    """Opens a web browser with search results."""
    try:
        import webbrowser
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return [color_text(f"Opened browser for: {query}", GREEN)]
    except Exception as e:
        return [color_text(f"Web search failed: {e}", RED)]


def launch_app(target_name):
    """Attempts to launch an application or file."""
    config = load_config()
    if not config.get('app_launcher_active', False):
        return [color_text("App Launcher is disabled in settings. Enable it in settings > Manage Features.", YELLOW)]

    if target_name.lower() in ('devmode', 'developer'):
        return [color_text("Launching Developer Mode...", CYAN)]
    elif target_name.lower() in ('gamemode', 'game'):
        return [color_text("Entering Game Mode...", BLUE)]

    if os.path.exists(target_name):
        return [color_text(f"Executing: {target_name}", GREEN)] + execute_command(f'"{target_name}"')

    if os.name == 'nt':
        return [color_text(f"Windows: Searching for '{target_name}'...", CYAN)]
    elif platform.system() == 'Darwin':
        return [color_text("macOS: Attempting 'open' command.", BLUE)] + execute_command(f"open -a '{target_name}'")
    else:
        return [color_text("Linux: Searching for '{target_name}'...", CYAN)] + execute_command(f"which {target_name} || echo 'Not found'")


def install_fastfetch():
    """Attempts to install fastfetch on the current platform."""
    if check_fastfetch_installed():
        print(color_text("fastfetch is already installed.", GREEN))
        return True

    print(color_text("Installing fastfetch...", CYAN))

    if os.name == 'nt':
        # Windows: try winget, then scoop, then choco
        for installer in ['winget', 'scoop', 'choco']:
            try:
                subprocess.run([installer, 'install', 'fastfetch', '-y'], check=True, capture_output=True)
                if check_fastfetch_installed():
                    print(color_text("fastfetch installed successfully!", GREEN))
                    return True
            except Exception:
                continue
        print(color_text("Failed to install fastfetch. Try: winget install fastfetch", RED))
        return False

    elif platform.system() == 'Darwin':
        try:
            subprocess.run(['brew', 'install', 'fastfetch'], check=True, capture_output=True)
            print(color_text("fastfetch installed successfully!", GREEN))
            return True
        except Exception:
            print(color_text("Failed to install fastfetch. Try: brew install fastfetch", RED))
            return False

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
                    print(color_text("fastfetch installed successfully!", GREEN))
                    return True
            except Exception:
                continue

        print(color_text("Failed to install fastfetch. Try your distro's package manager manually.", RED))
        return False


def check_fastfetch_installed():
    """Checks if fastfetch is installed."""
    if os.name == 'nt':
        # Check PATH on Windows
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


def run_fastfetch():
    """Runs fastfetch to display the OS logo and system info."""
    try:
        subprocess.run(['fastfetch'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(color_text("fastfetch not found. Run 'ff' command to install it.", YELLOW))


# --- Main Shell Loop ---

def get_shell_hints():
    """Returns OS-specific command hints."""
    if os.name == 'nt':
        return OS_COMMAND_HINTS['nt']
    return ['ls', 'clear', 'uname -a', 'top', 'df -h', 'ip a', 'ps aux']


def start_screen():
    """Main entry point - runs the interactive shell loop."""
    set_windows_ansi()

    # Check dependencies
    if not ensure_dependencies():
        input(color_text("Press Enter to exit...", RED))
        return

    # Check first-run setup
    if not MARKER_FILE.exists():
        clear()
        print(color_text("=== Welcome to Novium! ===", BOLD + CYAN))
        print(color_text("This is your first run. Let's get you set up.", BLUE))
        print()
        input(color_text("Press Enter to continue...", BLUE))
        render_setup_screen()
        MARKER_FILE.touch()

    # Load config
    config = load_config()

    # Splash
    splash_screen()

    # Detection
    run_system_detection()

    # Main loop
    last_output = []
    hints = get_shell_hints()

    while True:
        # Get stats
        stats = get_system_stats_snapshot()

        # Render shell with stats
        render_shell(stats, hints, last_output)

        # Print prompt
        print(color_text('novium> ', GREEN), end='', flush=True)

        # Read command (reliable cross-platform)
        try:
            command = input().strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            print(color_text("\nExiting Novium...", YELLOW))
            return

        if not command:
            continue

        parts = command.lower().split()

        # Built-in commands
        if command.lower() in ('exit', 'quit'):
            print(color_text("Goodbye!", GREEN))
            return
        elif command.lower() == 'help':
            last_output = []
        elif command.lower() == 'stats':
            last_output = []
        elif command.lower() == 'fan':
            last_output = []
        elif command.lower() == 'settings':
            last_output = []
        elif command.lower() == 'setup':
            last_output = []
        elif command.lower() == 'sysinfo':
            last_output = []
        elif command.lower() == 'nhome':
            last_output = []
        elif command.lower() == 'clear':
            last_output = []
        elif command.lower() == 'ff':
            # fastfetch command
            if check_fastfetch_installed():
                run_fastfetch()
            else:
                confirm = input(color_text("fastfetch not installed. Install it? (y/n): ", YELLOW)).strip().lower()
                if confirm == 'y':
                    install_fastfetch()
            last_output = []
        elif command.lower() == 'logo':
            # Logo switcher
            logo_choice = input(color_text("Choose logo: [1] Novium [2] OS (fastfetch) [3] None: ", GREEN)).strip()
            if logo_choice == '1':
                config['logo_mode'] = 'novium'
                save_config(config)
                print(color_text("Logo set to Novium.", GREEN))
            elif logo_choice == '2':
                config['logo_mode'] = 'os'
                save_config(config)
                print(color_text("Logo set to OS (fastfetch).", GREEN))
            elif logo_choice == '3':
                config['logo_mode'] = 'none'
                save_config(config)
                print(color_text("Logo disabled.", GREEN))
            else:
                print(color_text("Invalid choice.", RED))
            last_output = []
        elif command.lower().startswith('web '):
            query = " ".join(parts[1:])
            last_output = web_search(query)
        elif parts[0] == 'app' and len(parts) > 1:
            last_output = launch_app(" ".join(parts[1:]))
        elif parts[0] == 'color' and len(parts) > 1:
            color_name = parts[1].upper()
            if color_name in ('BLUE', 'CYAN', 'MAGENTA', 'GREEN', 'YELLOW', 'RED'):
                config['logo_color'] = color_name
                save_config(config)
                last_output = [color_text(f"Logo color set to {color_name}.", GREEN)]
            else:
                last_output = [color_text(f"Invalid color: {color_name}. Use: BLUE, CYAN, MAGENTA, GREEN, YELLOW, RED", RED)]
        elif parts[0] == 'install' and len(parts) > 1 and parts[1] == 'fastfetch':
            install_fastfetch()
            last_output = []
        elif command.lower() == 'nuke':
            confirm = input(color_text("This will completely remove Novium. Are you sure? Type 'YES' to confirm: ", RED)).strip()
            if confirm == 'YES':
                from config_manager import nuke_novium
                removed, failed = nuke_novium()
                if removed:
                    print(color_text("Removed:", GREEN))
                    for item in removed:
                        print(f"  - {item}")
                if failed:
                    print(color_text("Failed to remove:", RED))
                    for item in failed:
                        print(f"  - {item}")
                print(color_text("Novium has been completely removed.", GREEN))
                print(color_text("You can delete this folder manually.", YELLOW))
            else:
                print(color_text("Nuke cancelled.", YELLOW))
            last_output = []
        else:
            # Execute as system command
            last_output = execute_command(command)


if __name__ == '__main__':
    try:
        start_screen()
    except KeyboardInterrupt:
        print("\n" + color_text("Exiting Novium...", YELLOW))
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
