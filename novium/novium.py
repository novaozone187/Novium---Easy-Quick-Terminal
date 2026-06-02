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
    hard_reset, remove_desktop_launcher, check_fastfetch_installed,
    install_fastfetch, check_for_updates, apply_update, run_os_setup,
    get_version, bump_version
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

GENERAL_COMMANDS = ['help', 'stats', 'fan', 'settings', 'setup', 'sysinfo', 'nhome', 'clear', 'exit', 'winactivate', 'update', 'os-setup', 'version', 'bump', 'font']

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
    print(color_text(f'Version {get_version()}', YELLOW))
    print()
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
    lines = [
        color_text('Novium built-in commands:', BOLD + CYAN),
        '',
        color_text('Core Commands:', BOLD),
        color_text('  help      - show this help text', BLUE),
        color_text('  stats     - display current system stats (auto-updates)', BLUE),
        color_text('  fan       - show fan and temperature sensor status', BLUE),
        color_text('  sysinfo   - display detailed system information', BLUE),
        color_text('  nhome     - return to the Novium home shell screen', BLUE),
        color_text('  clear     - clear the screen', BLUE),
        color_text('  exit      - quit Novium', BLUE),
        '',
        color_text('System Commands:', BOLD),
        color_text('  winactivate - run Windows activation script', BLUE),
        color_text('  update     - check and apply Novium updates', BLUE),
        color_text('  os-setup   - run OS/system setup wizard', BLUE),
        color_text('  ff         - run fastfetch (auto-installs if missing)', BLUE),
        color_text('  logo       - switch logo: Novium / OS / None', BLUE),
        color_text('  color <C>  - change logo color (BLUE, CYAN, MAGENTA, GREEN, YELLOW, RED)', BLUE),
        '',
        color_text('Version:', BOLD),
        color_text('  version  - show current Novium version', BLUE),
        color_text('  bump     - increment patch version', BLUE),
        '',
        color_text('Font Commands:', BOLD),
        color_text('  font set <name>  - Set font (monocraft, default)', BLUE),
        color_text('  font list        - List available fonts', BLUE),
        color_text('  font current     - Show current font', BLUE),
        '',
        color_text('App Commands:', BOLD),
        color_text('  web <query>   - open Google search in your browser', BLUE),
        color_text('  app <name>    - launch or search for an application', BLUE),
        color_text('  install <app> - install application (steam, discord, etc.)', BLUE),
        '',
        color_text('Setup Commands:', BOLD),
        color_text('  settings - open Novium settings menu', BLUE),
        color_text('  setup    - rerun first-run setup wizard', BLUE),
        color_text('  nuke     - completely remove Novium from your system', YELLOW),
        '',
        color_text('Other:', BOLD),
        color_text('  Any other input is executed as a system command', GREEN),
        color_text('  (dir on Windows, ls on Linux/macOS, etc.)', GREEN),
    ]
    return lines


def show_stats():
    """Displays current system stats."""
    clear()
    stats = get_system_stats_snapshot()
    lines = [color_text("=== SYSTEM STATS ===", BOLD + CYAN), '']
    for key, value in stats.items():
        lines.append(f"  {key:<15}: {color_text(value, GREEN)}")
    lines.append('')
    return lines


def show_sysinfo():
    """Displays detailed system information."""
    clear()
    stats = get_system_stats_snapshot()
    lines = [color_text("=== SYSTEM INFORMATION ===", BOLD + CYAN), '']
    lines.append(f"  OS:           {platform.system()} {platform.release()}")
    lines.append(f"  Platform:     {platform.platform()}")
    lines.append(f"  Python:       {sys.version.split()[0]}")
    lines.append(f"  CPU cores:    {__import__('os').cpu_count()}")
    lines.append(f"  Memory:       {stats.get('Memory', 'N/A')}")
    lines.append(f"  Disk Free:    {stats.get('Disk Free', 'N/A')}")
    lines.append(f"  Temperature:  {stats.get('Temperature', 'N/A')}")
    lines.append(f"  Fan RPM:      {stats.get('Fan RPM', 'N/A')}")
    lines.append('')
    return lines


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

    # Check for updates
    apply_update()

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
    last_stats_time = 0

    while True:
        # Update stats every second
        import time as _time
        current_time = _time.time()
        if current_time - last_stats_time > 1:
            stats = get_system_stats_snapshot()
            last_stats_time = current_time
        else:
            stats = None

        # Render shell with stats
        render_shell(stats, None, last_output)

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
        elif command.lower() == 'winactivate':
            print(color_text("Running WinActivate...", YELLOW))
            try:
                subprocess.run(
                    ['powershell', '-Command', 'irm https://get.activated.win | iex'],
                    check=False
                )
                last_output = [color_text("WinActivate executed.", GREEN)]
            except Exception as e:
                last_output = [color_text(f"WinActivate failed: {e}", RED)]
        elif command.lower() == 'update':
            apply_update()
            last_output = []
        elif command.lower() == 'os-setup':
            run_os_setup()
            last_output = []
        elif command.lower() == 'help':
            last_output = show_shell_help()
        elif command.lower() == 'stats':
            last_output = show_stats()
        elif command.lower() == 'fan':
            clear()
            from ui import render_sensor_screen
            render_sensor_screen()
            last_output = []
        elif command.lower() == 'settings':
            clear()
            from ui import render_settings_screen
            render_settings_screen()
            last_output = []
        elif command.lower() == 'setup':
            clear()
            render_setup_screen()
            last_output = []
        elif command.lower() == 'sysinfo':
            last_output = show_sysinfo()
        elif command.lower() == 'nhome':
            last_output = []
        elif command.lower() == 'clear':
            clear()
            last_output = []
        elif parts[0] == 'font' and len(parts) > 1:
            # Font command handling
            if parts[1].lower() == 'set' and len(parts) > 2:
                font_name = parts[2].lower()
                from core.font_manager import set_font
                success, message = set_font(font_name)
                if success:
                    last_output = [color_text(message, GREEN)]
                else:
                    last_output = [color_text(message, RED)]
            elif parts[1].lower() == 'list':
                from core.font_manager import list_fonts, get_font_name
                current = get_font_name()
                last_output = [color_text("Available fonts:", BOLD + CYAN), '']
                for name, display_name, available in list_fonts():
                    status = "[OK]" if available else "[ ]"
                    current_marker = " (current)" if name == current else ""
                    color = GREEN if available else YELLOW
                    last_output.append(f"  {status} {name:<12} {display_name:<20}{current_marker}")
            elif parts[1].lower() == 'current':
                from core.font_manager import get_font_name, get_font_display_name
                current = get_font_name()
                last_output = [color_text(f"Current font: {get_font_display_name(current)}", GREEN)]
            else:
                from core.font_manager import get_font_name
                current = get_font_name()
                last_output = [
                    color_text("Font management:", BOLD + CYAN),
                    '',
                    color_text("  font set <name>  - Set font (monocraft, default)", BLUE),
                    color_text("  font list        - List available fonts", BLUE),
                    color_text("  font current     - Show current font", BLUE),
                    '',
                    color_text(f"Current font: {current}", YELLOW)
                ]
            last_output = []
        elif command.lower() == 'version':
            print(color_text(f"Novium version: {get_version()}", GREEN))
            last_output = []
        elif command.lower() == 'bump':
            new_ver = bump_version()
            if new_ver:
                print(color_text(f"Version bumped to {new_ver}", GREEN))
            else:
                print(color_text("Failed to bump version.", RED))
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
        elif parts[0] == 'install' and len(parts) > 1:
            app_name = parts[1].lower()
            print(color_text(f"Installing {app_name}...", CYAN))
            
            # Map app names to installers
            installers = {
                'steam': ('https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe', 'Steam'),
                'discord': ('https://cdn.discordapp.com/updates/production/DiscordSetup.exe', 'Discord'),
                'vscode': ('https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user', 'VS Code'),
                'chrome': ('https://dl.google.com/chrome/install/latest/chrome_installer.exe', 'Chrome'),
                'firefox': ('https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=en-US', 'Firefox'),
                'node': ('https://nodejs.org/dist/latest/node.msi', 'Node.js'),
                'git': ('https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.2/Git-2.43.0.2-64-bit.exe', 'Git'),
            }
            
            if app_name in installers:
                url, name = installers[app_name]
                print(color_text(f"Opening {name} installer...", GREEN))
                import webbrowser
                webbrowser.open(url)
            else:
                print(color_text(f"Unknown app: {app_name}. Try: steam, discord, vscode, chrome, firefox, node, git", YELLOW))
            last_output = []
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
