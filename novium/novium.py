# novium.py - Main application logic for Novium
# Clean, modular, no duplication

import os
import sys
import time
import subprocess
import platform
import traceback
from pathlib import Path

# Local imports
from utils import (
    color_text, BOLD, BLUE, CYAN, GREEN, YELLOW, RED, MAGENTA, RESET,
    clear, set_windows_ansi, apply_theme, THEME,
    draw_box, draw_header, draw_table, render_status_bar, read_key
)
from config_manager import (
    load_config, save_config, ensure_dependencies, MARKER_FILE,
    create_desktop_launcher, enable_autostart, remove_autostart,
    hard_reset, remove_desktop_launcher, check_fastfetch_installed,
    install_fastfetch, check_for_updates, apply_update, run_os_setup,
    get_version
)
from system_monitor import (
    get_system_stats_snapshot, get_temperature, get_fan_rpm,
    get_temperature_sensors, get_fan_sensors, check_browser_installed,
    detect_linux_distro
)
from ui import (
    display_logo, render_initial_home,
    render_sensor_screen, render_settings_screen, render_setup_screen,
    _network_connection_screen
)
from network import get_network, DISCORD_INVITE

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

GENERAL_COMMANDS = ['help', 'stats', 'fan', 'settings', 'setup', 'sysinfo', 'nhome', 'clear', 'exit', 'winactivate', 'update', 'os-setup', 'version', 'font', 'perfcheck', 'seccheck']

OS_COMMAND_HINTS = {
    'nt': ['dir', 'cls', 'ipconfig', 'tasklist', 'systeminfo'],
    'posix': ['ls', 'clear', 'uname -a', 'top', 'df -h']
}


# --- Splash & Detection ---

def splash_screen():
    """Displays the splash screen (skippable with Enter)."""
    set_windows_ansi()
    clear()
    display_logo(FULL_LOGO, delay=0.002)
    print()
    print(color_text('Welcome to Novium', CYAN))
    print(color_text(f'Version {get_version()}', YELLOW))
    print()
    input(color_text('Press Enter to continue...', YELLOW))


def run_system_detection():
    """Runs environment detection and displays results."""
    set_windows_ansi()
    detected = {}
    detected['Web Browser'] = check_browser_installed()
    try:
        import psutil
        detected['psutil'] = True
    except ImportError:
        detected['psutil'] = False
    try:
        import websocket
        detected['websocket-client'] = True
    except ImportError:
        detected['websocket-client'] = False
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

    input(color_text("Press Enter to continue...", BLUE))
    return detected


# --- Shell Commands ---

def show_shell_help():
    """Prints built-in command help."""
    clear()
    top_lines = [
        color_text(f"  Novium v{get_version()}  —  type a command and press Enter", BOLD + CYAN),
        color_text("  Unrecognized commands are passed to your system shell", BLUE),
    ]
    draw_box(top_lines, title="NOVIUM HELP", border_color=THEME["secondary"])
    print()

    sections = [
        ("SYSTEM", [
            ("stats", "Live CPU, memory, disk, temp & fan monitor (Q to stop)"),
            ("fan", "Temperature and fan sensor dashboard"),
            ("sysinfo", "Detailed system information overview"),
            ("perfcheck", "Run performance health checks with auto-fix"),
            ("seccheck", "Scan for security issues and suspicious activity"),
            ("ff", "Launch fastfetch (auto-installs if missing)"),
        ]),
        ("NETWORK", [
            ("scanLAN [-d]", "Scan LAN for devices — add -d for deep TCP probe"),
            ("novium connect [url]", "Connect to Novium Network"),
            ("novium status", "Show connection status and client info"),
            ("novium disconnect", "Disconnect from Novium Network"),
            ("novium invite", "Join the Novium Discord server"),
        ]),
        ("APPS & TOOLS", [
            ("web <query>", "Search Google from your terminal"),
            ("app <name>", "Launch or search for an app"),
            ("install <app>", "Quick install: steam, discord, vscode, chrome, firefox, node, git"),
            ("font set <name>", "Set terminal font (monocraft, default)"),
            ("font list", "List available fonts"),
            ("font current", "Show currently active font"),
        ]),
        ("CUSTOMIZE", [
            ("settings", "Open settings menu (toggles, network, shortcuts)"),
            ("setup", "Re-run first-time setup wizard"),
            ("color <C>", "Change logo color: BLUE, CYAN, MAGENTA, GREEN, YELLOW, RED"),
            ("logo", "Switch logo: Novium / OS (fastfetch) / None"),
            ("os-setup", "Run OS-specific setup and configuration"),
        ]),
        ("SESSION", [
            ("nhome", "Return to Novium home screen"),
            ("clear", "Clear terminal screen"),
            ("version", "Show current Novium version"),
            ("help", "Display this help text"),
            ("exit", "Quit Novium"),
        ]),
        ("MAINTENANCE", [
            ("update", "Check GitHub for Novium updates"),
            ("winactivate", "Run Windows activation script"),
            ("nrestart", "Restart Novium (applies code updates)"),
            ("nuke", "Permanently remove Novium from your system"),
        ]),
    ]

    for section_name, commands in sections:
        print(color_text(f"  {section_name}", BOLD + THEME["secondary"]))
        draw_table(
            [color_text("Command", THEME["highlight"]), color_text("Description", THEME["highlight"])],
            [[color_text(cmd, THEME["secondary"]), color_text(desc, BLUE)] for cmd, desc in commands],
            border_color=THEME["secondary"]
        )
        print()

    print(color_text("  Any other input runs as a system command", GREEN))
    print(color_text("  (dir, ls, ipconfig, uname -a, etc.)", GREEN))
    print()


def show_sysinfo():
    """Displays detailed system information."""
    stats = get_system_stats_snapshot()
    lines = [
        f"  OS           : {platform.system()} {platform.release()}",
        f"  Platform     : {platform.platform()}",
        f"  Python       : {sys.version.split()[0]}",
        f"  CPU cores    : {os.cpu_count()}",
        f"  Memory       : {color_text(stats.get('Memory', 'N/A'), THEME['stat_value'])}",
        f"  Disk Free    : {color_text(stats.get('Disk Free', 'N/A'), THEME['stat_value'])}",
        f"  Temperature  : {color_text(stats.get('Temperature', 'N/A'), THEME['stat_value'])}",
        f"  Fan RPM      : {color_text(stats.get('Fan RPM', 'N/A'), THEME['stat_value'])}",
    ]
    draw_box(lines, title="SYSTEM INFORMATION", border_color=THEME["border"])


def execute_command(cmd):
    """Executes a system command and prints output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30
        )
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                print(color_text(line, YELLOW))
        if not result.stdout and not result.stderr:
            print(color_text("Command executed successfully.", GREEN))
    except subprocess.TimeoutExpired:
        print(color_text("Command timed out.", RED))
    except Exception as e:
        print(color_text(f"Error: {e}", RED))


def web_search(query):
    """Opens a web browser with search results."""
    try:
        import webbrowser
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        print(color_text(f"Opened browser for: {query}", GREEN))
    except Exception as e:
        print(color_text(f"Web search failed: {e}", RED))


def launch_app(target_name):
    """Attempts to launch an application or file."""
    config = load_config()
    if not config.get('app_launcher_active', False):
        print(color_text("App Launcher is disabled in settings. Enable it in settings > Manage Features.", YELLOW))
        return

    if target_name.lower() in ('devmode', 'developer'):
        print(color_text("Launching Developer Mode...", CYAN))
    elif target_name.lower() in ('gamemode', 'game'):
        print(color_text("Entering Game Mode...", BLUE))
    elif os.path.exists(target_name):
        print(color_text(f"Executing: {target_name}", GREEN))
        execute_command(f'"{target_name}"')
    elif os.name == 'nt':
        print(color_text(f"Windows: Searching for '{target_name}'...", CYAN))
    elif platform.system() == 'Darwin':
        print(color_text("macOS: Attempting 'open' command.", BLUE))
        execute_command(f"open -a '{target_name}'")
    else:
        print(color_text(f"Linux: Searching for '{target_name}'...", CYAN))
        execute_command(f"which {target_name} || echo 'Not found'")


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
    apply_theme(config)

    # Splash
    splash_screen()

    # Detection
    run_system_detection()

    # Network auto-connect
    net = get_network()
    if config.get("network", {}).get("enabled", False):
        url = config["network"].get("server_url", "ws://novium-network.duckdns.org:8765")
        ok, msg = net.connect(url)
        if ok:
            print(color_text(f"  {msg}", GREEN))
        else:
            print(color_text(f"  {msg}", YELLOW))

    net.add_listener(lambda event, data: None)

    render_initial_home()
    print()

    if not net.connected:
        print(color_text("  Type 'network connect' to join Novium Network, or 'help' for commands.", YELLOW))
        print()

    # Main terminal loop
    while True:
        if net._pending_code and not net.verified:
            saved_code = net._pending_code
            net._pending_code = None
            clear()
            draw_box([
                color_text(f"  Challenge code: {saved_code}", BOLD + THEME["highlight"]),
                "",
                color_text(f"  1. Open Discord -> verification channel", THEME["secondary"]),
                color_text(f"  2. Click Confirm Code -> enter the code above", THEME["secondary"]),
                color_text(f"  3. You'll get the Novium Verified role + private channel", THEME["secondary"]),
                "",
                color_text(f"  Code expires in 5 minutes.", THEME["warning"]),
            ], title="VERIFICATION CODE", border_color=THEME["highlight"])
            input(color_text("  Press Enter to continue...", CYAN))
            print()
            continue

        stats = get_system_stats_snapshot()
        render_status_bar(
            version=get_version(),
            connected=net.connected,
            client_id=net.client_id,
            verified=net.verified,
            cpu=stats.get("CPU", ""),
            mem=stats.get("Memory", "")
        )
        print(color_text('novium> ', GREEN), end='', flush=True)

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
                print(color_text("WinActivate executed.", GREEN))
            except Exception as e:
                print(color_text(f"WinActivate failed: {e}", RED))
        elif command.lower() == 'update':
            apply_update(interactive=True)
        elif command.lower() == 'os-setup':
            run_os_setup()
        elif command.lower() == 'perfcheck':
            from system_monitor import run_performance_check as _perfcheck
            print(color_text("  Running performance check...", CYAN))
            _results = _perfcheck()
            _fixable = []
            for _r in _results:
                _icon = color_text("PASS", GREEN) if _r["status"] == "OK" else (color_text("WARN", YELLOW) if _r["status"] == "WARNING" else color_text("FAIL", RED))
                print(f"  {_icon}  {_r['check']:<18}: {_r['message']}")
                if _r.get("fix_cmd"):
                    _fixable.append(_r)
            if _fixable:
                print()
                print(color_text(f"  {len(_fixable)} issue(s) can be auto-fixed.", YELLOW))
                _confirm = input(color_text("  Apply fixes? (y/n): ", YELLOW)).strip().lower()
                if _confirm == 'y':
                    for _r in _fixable:
                        print(color_text(f"  → {_r['fix']}...", CYAN))
                        try:
                            subprocess.run(_r["fix_cmd"], timeout=30)
                            print(color_text(f"  ✓ Done", GREEN))
                        except Exception as _e:
                            print(color_text(f"  ✗ Failed: {_e}", RED))
            del _perfcheck, _results, _fixable, _r, _icon, _confirm
        elif command.lower() == 'seccheck':
            from system_monitor import run_security_check as _seccheck
            print(color_text("  Running security scan...", CYAN))
            _sec_results = _seccheck()
            for _r in _sec_results:
                _icon = color_text("PASS", GREEN) if _r["status"] == "OK" else (color_text("WARN", YELLOW) if _r["status"] == "WARNING" else color_text("FAIL", RED))
                print(f"  {_icon}  {_r['check']:<24}: {_r['message']}")
            del _seccheck, _sec_results, _r, _icon
        elif command.lower() == 'help':
            show_shell_help()
        elif command.lower() == 'stats':
            while True:
                clear()
                stats = get_system_stats_snapshot()
                lines = [f"  {k:<15}: {color_text(v, THEME['stat_value'])}" for k, v in stats.items()]
                draw_box(lines, title="SYSTEM STATS (LIVE)", border_color=THEME["border"])
                print(color_text("  Press Q to stop", YELLOW))
                key = read_key(timeout=2)
                if key and key.lower() == 'q':
                    break
        elif command.lower() == 'fan':
            clear()
            from ui import render_sensor_screen
            render_sensor_screen()
        elif command.lower() == 'settings':
            clear()
            from ui import render_settings_screen
            render_settings_screen()
        elif command.lower() == 'setup':
            clear()
            render_setup_screen()
        elif command.lower() == 'sysinfo':
            show_sysinfo()
        elif command.lower() == 'nhome':
            render_initial_home()
        elif command.lower() == 'clear':
            clear()
        elif command.lower() == 'nrestart':
            print(color_text("  Restarting Novium...", CYAN))
            import subprocess as _sp, sys as _sys, os as _os, signal as _sig, time as _time
            _sys.stdout.flush()
            script = _os.path.abspath(_sys.argv[0])
            if _os.name == 'nt':
                _sp.Popen(
                    [_sys.executable, script] + _sys.argv[1:],
                    creationflags=_sp.CREATE_NEW_CONSOLE
                )
                _time.sleep(1)
                try:
                    _os.kill(_os.getppid(), _sig.SIGTERM)
                except Exception:
                    pass
            else:
                _os.execv(_sys.executable, [_sys.executable, script] + _sys.argv[1:])
            _os._exit(0)
        elif command.lower() == 'scanlan':
            from network_scanner import scan as net_scan
            deep = '--deep' in parts or '-d' in parts
            print(color_text("  Scanning LAN...", CYAN))
            devices, error = net_scan(deep=deep)
            if error:
                print(color_text(f"  Scan failed: {error}", RED))
            elif not devices:
                print(color_text("  No devices found on network.", YELLOW))
            else:
                print(color_text(f"  Found {len(devices)} device(s):\n", BOLD + GREEN))
                has_ports = any(d.get("ports") for d in devices)
                if has_ports:
                    headers = ["IP Address", "Hostname", "MAC Address", "Type", "Ports"]
                else:
                    headers = ["IP Address", "Hostname", "MAC Address", "Type"]
                rows = []
                for d in devices:
                    ip = d["ip"]
                    hostname = d.get("hostname", "N/A")[:23]
                    mac = d["mac"]
                    dtype = d.get("type", "Unknown")
                    c = GREEN if dtype not in ("Unknown", "N/A") else YELLOW
                    ports = d.get("ports", [])
                    ports_str = ",".join(str(p) for p in ports[:4]) if ports else ""
                    if ports_str:
                        ports_str += "+" if len(ports) > 4 else ""
                    row = [str(ip), str(hostname), str(mac), color_text(dtype, c)]
                    if has_ports:
                        row.append(color_text(ports_str, CYAN))
                    rows.append(row)
                draw_table(headers, rows, border_color=THEME["border"])
        elif parts[0] == 'font' and len(parts) > 1:
            if parts[1].lower() == 'set' and len(parts) > 2:
                font_name = parts[2].lower()
                from core.font_manager import set_font
                success, message = set_font(font_name)
                print(color_text(message, GREEN if success else RED))
            elif parts[1].lower() == 'list':
                from core.font_manager import list_fonts, get_font_name
                current = get_font_name()
                print(color_text("Available fonts:", BOLD + CYAN))
                for name, display_name, available in list_fonts():
                    status = "[OK]" if available else "[ ]"
                    current_marker = " (current)" if name == current else ""
                    c = GREEN if available else YELLOW
                    print(f"  {status} {name:<12} {display_name:<20}{current_marker}")
            elif parts[1].lower() == 'current':
                from core.font_manager import get_font_name, get_font_display_name
                current = get_font_name()
                print(color_text(f"Current font: {get_font_display_name(current)}", GREEN))
            else:
                from core.font_manager import get_font_name
                current = get_font_name()
                print(color_text("Font management:", BOLD + CYAN))
                print(color_text("  font set <name>  - Set font (monocraft, default)", BLUE))
                print(color_text("  font list        - List available fonts", BLUE))
                print(color_text("  font current     - Show current font", BLUE))
                print(color_text(f"Current font: {current}", YELLOW))
        elif command.lower() == 'version':
            print(color_text(f"Novium version: {get_version()}", GREEN))
        elif command.lower() == 'ff':
            if check_fastfetch_installed():
                run_fastfetch()
            else:
                confirm = input(color_text("fastfetch not installed. Install it? (y/n): ", YELLOW)).strip().lower()
                if confirm == 'y':
                    install_fastfetch()
        elif command.lower() == 'logo':
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
        elif command.lower().startswith('web '):
            web_search(" ".join(parts[1:]))
        elif parts[0] == 'app' and len(parts) > 1:
            launch_app(" ".join(parts[1:]))
        elif parts[0] == 'color' and len(parts) > 1:
            color_name = parts[1].upper()
            if color_name in ('BLUE', 'CYAN', 'MAGENTA', 'GREEN', 'YELLOW', 'RED'):
                config['logo_color'] = color_name
                save_config(config)
                print(color_text(f"Logo color set to {color_name}.", GREEN))
            else:
                print(color_text(f"Invalid color: {color_name}. Use: BLUE, CYAN, MAGENTA, GREEN, YELLOW, RED", RED))
        elif parts[0] == 'install' and len(parts) > 1:
            if parts[1].lower() == 'fastfetch':
                install_fastfetch()
            else:
                app_name = parts[1].lower()
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
        elif command.lower() == 'nuke':
            print(color_text("WARNING: This will completely remove Novium from your system.", BOLD + RED))
            print()
            confirm = input(color_text("Type 'YES' to confirm: ", RED)).strip()
            if confirm != 'YES':
                print(color_text("Nuke cancelled.", YELLOW))
                break
            from config_manager import nuke_novium
            removed, failed, terminated_pids, cleanup_script = nuke_novium()
            print()
            if terminated_pids:
                print(color_text(f"  Terminated {len(terminated_pids)} Novium process(es).", GREEN))
            if removed:
                print(color_text(f"  Removed {len(removed)} item(s).", GREEN))
            if failed:
                print(color_text(f"  {len(failed)} item(s) failed (will be cleaned on reboot):", YELLOW))
                for item in failed:
                    print(f"    - {item}")
            if cleanup_script:
                try:
                    if os.name == 'nt':
                        subprocess.Popen([cleanup_script], creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        subprocess.Popen(['bash', cleanup_script])
                except Exception as e:
                    print(color_text(f"  Cleanup script failed: {e}", RED))
            print()
            print(color_text("Novium has been removed.", GREEN))
            print(color_text("Close this terminal and delete the novium folder manually.", YELLOW))
            break
        elif parts[0] in ('network', 'novium'):
            from ui import _network_settings
            net = get_network()
            if len(parts) == 1 or parts[1] == 'gui':
                _network_settings()
            elif parts[1] == 'status':
                print(color_text(net.status_text(), CYAN))
            elif parts[1] == 'connect':
                if net.connected:
                    print(color_text("Already connected.", YELLOW))
                else:
                    url = parts[2] if len(parts) > 2 else config.get("network", {}).get("server_url", "ws://novium-network.duckdns.org:8765")
                    _network_connection_screen(net, url)
                    if net.connected:
                        cfg = load_config()
                        cfg.setdefault("network", {})["enabled"] = True
                        cfg["network"]["server_url"] = url
                        save_config(cfg)
            elif parts[1] == 'disconnect':
                if not net.connected:
                    print(color_text("Not connected.", YELLOW))
                else:
                    print(color_text("  Why are you disconnecting?", CYAN))
                    reason = input(color_text("  Reason: ", GREEN)).strip()
                    if not reason:
                        reason = "No reason provided"
                    net.disconnect_with_reason(reason)
                    cfg = load_config()
                    cfg.setdefault("network", {})["enabled"] = False
                    save_config(cfg)
                    print(color_text(f"Disconnected. Reason logged: {reason}", YELLOW))
            elif parts[1] == 'invite':
                import webbrowser
                webbrowser.open(DISCORD_INVITE)
                print(color_text(f"Opening Discord invite: {DISCORD_INVITE}", GREEN))
            else:
                print(color_text("Usage: novium [connect <url>|disconnect|status|invite]", YELLOW))
        else:
            execute_command(command)

        print()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Novium - Easy Quick Terminal")
    parser.add_argument("--server", "-s", help="Novium Network WebSocket URL (overrides config)")
    args, _ = parser.parse_known_args()
    if args.server:
        cfg = load_config()
        cfg.setdefault("network", {})["server_url"] = args.server
        save_config(cfg)
    try:
        start_screen()
    except KeyboardInterrupt:
        print("\n" + color_text("Exiting Novium...", YELLOW))
    except Exception as e:
        net = get_network()
        tb = traceback.format_exc()
        if net.connected:
            net.send_error(str(e), tb)
        print(f"\n[ERROR] {e}")
        traceback.print_exc()
