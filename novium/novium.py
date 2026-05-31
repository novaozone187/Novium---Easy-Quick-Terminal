import os
import sys
import time
import json
import shutil
import ctypes
import platform
import subprocess
import importlib
from pathlib import Path
from functools import lru_cache

# Versuche rich zu importieren, ansonsten Fallback
try:
    from rich.console import Console
except ImportError:
    Console = None

# Fallback für die Utils, falls utils.py nicht existiert
try:
    from utils import color_text, BOLD, BLUE, CYAN, GREEN, YELLOW, RED, MAGENTA, RESET
except ImportError:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    def color_text(text, color): return f"{color}{text}{RESET}"

# Globals
psutil = None
COLOR_THEMES = {
    'BLUE': BLUE, 'CYAN': CYAN, 'MAGENTA': MAGENTA, 
    'GREEN': GREEN, 'YELLOW': YELLOW, 'RED': RED
}

# -----------------------
# LOGOS
# -----------------------
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

# -----------------------
# CONFIG & SETTINGS HANDLERS
# -----------------------
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
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with CONFIG_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def pip_install_requirements(requirements_file=REQUIREMENTS_FILE, user=False):
    if not requirements_file.exists():
        return False
    command = [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)]
    if user:
        command.append('--user')
    try:
        subprocess.check_call(command)
        return True
    except Exception:
        return False

def ensure_dependencies():
    global psutil
    if psutil is not None:
        return True
    print(color_text('Missing required dependency: psutil', YELLOW))
    if not REQUIREMENTS_FILE.exists():
        print(color_text('requirements.txt not found. Cannot auto-install dependencies.', RED))
        return False
    print(color_text('Attempting automatic dependency installation...', CYAN))
    if pip_install_requirements():
        try:
            psutil = importlib.import_module('psutil')
            print(color_text('Dependencies installed successfully.', GREEN))
            return True
        except Exception:
            pass
    if os.name != 'nt':
        print(color_text('Retrying installation with --user flag...', CYAN))
        if pip_install_requirements(user=True):
            try:
                psutil = importlib.import_module('psutil')
                print(color_text('Dependencies installed successfully.', GREEN))
                return True
            except Exception:
                pass
    print(color_text('Automatic dependency installation failed. Run `python install.py` or `python -m pip install -r requirements.txt`.', RED))
    return False

# -----------------------
# UTILITIES
# -----------------------
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def center_print(text: str):
    cols = shutil.get_terminal_size().columns
    for line in text.splitlines():
        clean = line
        pad = max(0, (cols - len(clean)) // 2)
        print(" " * pad + line)

def set_windows_ansi():
    if os.name != 'nt':
        return
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint()
    if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)

def execute_system_command(command):
    os.system(command)
    return []

def color_logo(logo_str):
    config = load_config()
    c_name = config.get('logo_color', 'BLUE')
    return color_text(logo_str, COLOR_THEMES.get(c_name, BLUE))

def cursor_move(row, col):
    print(f"\033[{row};{col}H", end="")

def clear_line():
    print("\033[K", end="")

def redraw_prompt(row, buffer):
    cursor_move(row, 1)
    clear_line()
    print(color_text('novium> ', GREEN) + buffer, end='', flush=True)

# -----------------------
# HARDWARE & SYSTEM MONITORING
# -----------------------
@lru_cache(maxsize=None)
def detect_hardware():
    info = {}
    info['cpu_count'] = psutil.cpu_count(logical=True) if psutil else os.cpu_count()
    if psutil:
        info['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        info['mem_percent'] = psutil.virtual_memory().percent
        info['total_mem_gb'] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        disk = shutil.disk_usage(str(Path.home()))
        info['disk_free_gb'] = round(disk.free / (1024 ** 3), 1)
    else:
        info['cpu_percent'] = 'N/A'
        info['mem_percent'] = 'N/A'
        info['total_mem_gb'] = 'N/A'
        info['disk_free_gb'] = 'N/A'
    return info

def get_system_stats_snapshot():
    hw = detect_hardware()
    cpu_pct = hw.get('cpu_percent', 'N/A')
    mem_pct = hw.get('mem_percent', 'N/A')
    total_mem = hw.get('total_mem_gb', 'N/A')
    disk_free = hw.get('disk_free_gb', 'N/A')
    temp = get_temperature()
    fan = get_fan_rpm()
    return {
        "CPU": f"{cpu_pct}%",
        "Memory": f"{mem_pct}% ({total_mem}GB)",
        "Disk Free": f"{disk_free} GB",
        "Temperature": str(temp),
        "Fan RPM": str(fan),
        "Time": time.strftime('%H:%M:%S')
    }

def get_temperature():
    if not psutil or not hasattr(psutil, 'sensors_temperatures'):
        return 'N/A'
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return 'N/A'
        for k, v in temps.items():
            if v:
                return f"{v[0].current}C"
    except Exception:
        pass
    return 'N/A'

def get_fan_rpm():
    fans = get_fan_sensors()
    return fans[0][1] if fans else 'N/A'

def get_temperature_sensors():
    if not psutil or not hasattr(psutil, 'sensors_temperatures'):
        return []
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return []
        sensors = []
        for name, entries in temps.items():
            for entry in entries:
                label = entry.label or name
                sensors.append((label, f"{entry.current}C"))
        return sensors
    except Exception:
        return []

def get_fan_sensors():
    if not psutil or not hasattr(psutil, 'sensors_fans'):
        return []
    try:
        fans = psutil.sensors_fans()
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

def format_sensor_status():
    lines = []
    fans = get_fan_sensors()
    temps = get_temperature_sensors()
    if fans:
        lines.append(color_text('Fan sensors:', BOLD + BLUE))
        for label, value in fans:
            lines.append(f"  {label}: {color_text(value, CYAN)}")
    else:
        lines.append(color_text('No fan sensors available.', YELLOW))
    lines.append('')
    if temps:
        lines.append(color_text('Temperature sensors:', BOLD + BLUE))
        for label, value in temps:
            lines.append(f"  {label}: {color_text(value, MAGENTA)}")
    else:
        lines.append(color_text('No temperature sensors available.', YELLOW))
    return lines

# -----------------------
# APPLICATION & WEB (Phase 2)
# -----------------------
def check_browser_installed() -> bool:
    if os.name == 'nt':
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        return any(Path(p).exists() for p in paths)
    for name in ("google-chrome", "chrome", "chromium", "firefox"):
        try:
            res = subprocess.run(["which", name], capture_output=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass
    return False

def web_search(query):
    try:
        import webbrowser
        if not hasattr(webbrowser, 'open'):
             return [color_text("Webbrowser module is missing or unusable.", RED)]
        
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return [color_text("Opened web browser for search query: " + query, GREEN)]
    except Exception as e:
        return [color_text(f"Error opening browser: {e}", RED)]

def launch_app(target_name):
    config = load_config()
    if not config.get('app_launcher_active', False):
        return [color_text("App Launcher is disabled in settings.", YELLOW)]
    
    if target_name.lower() == 'devmode':
        return [color_text("Launching Developer Mode...", CYAN)]
    elif target_name.lower() == 'gamemode':
        return [color_text("Entering Game Mode (OS specific optimization)...", BLUE)]
        
    if os.path.exists(target_name):
        return [color_text(f"Found file: {target_name}. Executing...", GREEN)] + execute_system_command(f'"{target_name}"')
        
    if os.name == 'nt':
        return [color_text(f"Windows lookup: Searching for '{target_name}' via system search...", CYAN)]
    elif platform.system() == 'Darwin':
        return [color_text("macOS lookup: Attempting 'open' command.", BLUE)] + execute_system_command(f"open '{target_name}'")
    else:
        return [color_text("Linux lookup: Attempting to find package/app via 'find' or similar.", BLUE)] + execute_system_command(f"which {target_name} || echo 'Not found'")

# -----------------------
# SETUP & SETTINGS FLOWS
# -----------------------
def create_desktop_launcher():
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
    except Exception as e:
        print(f"Failed to create launcher: {e}")

def get_windows_startup_folder():
    appdata = os.getenv('APPDATA')
    if appdata:
        return Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    home = Path.home()
    return home / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'

def remove_autostart():
    home = Path.home()
    if os.name == 'nt':
        target = get_windows_startup_folder() / 'run_novium.bat'
        if target.exists():
            try:
                target.unlink()
            except Exception:
                pass
    else:
        desktop_file = home / '.config' / 'autostart' / 'novium.desktop'
        if desktop_file.exists():
            try:
                desktop_file.unlink()
            except Exception:
                pass

def enable_autostart():
    # Placeholder für Autostart-Logik, da diese im Original unvollständig war
    print(color_text("Autostart enable logic not fully implemented yet.", YELLOW))

def hard_reset():
    for path in (MARKER_FILE, CONFIG_FILE):
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
    remove_autostart()
    print(color_text("Hard reset completed. Next run will behave like a fresh install.", GREEN))

def customize_experience():
    config = load_config()
    current = config.get('logo_color', 'BLUE')
    options = [
        ('1', 'BLUE'), ('2', 'CYAN'), ('3', 'MAGENTA'),
        ('4', 'GREEN'), ('5', 'YELLOW'), ('6', 'RED'),
        ('7', 'Skip customization')
    ]
    while True:
        clear()
        print(color_text('=== CUSTOMIZE YOUR EXPERIENCE ===', BOLD + CYAN))
        print()
        for key, name in options:
            if name == 'Skip customization':
                print(color_text(f'{key}) {name}', BLUE))
            else:
                selected = ' (current)' if current == name else ''
                print(color_text(f'{key}) {name}{selected}', COLOR_THEMES.get(name, BLUE)))
        print()
        choice = input(color_text('Select > ', GREEN)).strip()
        if choice == '7':
            break
        mapping = {opt[0]: opt[1] for opt in options if opt[1] != 'Skip customization'}
        if choice in mapping:
            config['logo_color'] = mapping[choice]
            save_config(config)
            current = mapping[choice]
            print(color_text(f'Logo color set to {current}.', GREEN))
            time.sleep(1)
            break
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)

def manage_features():
    set_windows_ansi()
    while True:
        clear()
        config = load_config()
        print(color_text("=== NOVIUM FEATURE TOGGLES ===", BOLD + CYAN))
        print()
        
        features = [
            ("Hardware Monitoring (Stats/Fan)", 'hardware_monitoring'),
            ("Web Search/Lookup (web command)", 'web_search_enabled'),
            ("App Launcher/File Lookup (app <name>)", 'app_launcher_active'),
            ("Autostart Integration (Startup)", 'autostart_enabled')
        ]
        
        for i, (label, key) in enumerate(features, 1):
            enabled = config.get(key, False)
            status_color = GREEN if enabled else RED
            print(color_text(f"[{i}] {label}:", BLUE))
            print(f"  - Status: {color_text('Enabled' if enabled else 'Disabled', status_color)}")
            print(color_text("--------------------------------------", YELLOW))
            
        print(color_text("[5] Back", MAGENTA))
        print()
        
        choice = input(color_text("Toggle Feature (1-4) or 5 to go back > ", GREEN)).strip()
        
        if choice in ['1', '2', '3', '4']:
            key = features[int(choice)-1][1]
            config[key] = not config.get(key, False)
            save_config(config)
            print(color_text(f"\nToggled {features[int(choice)-1][0]}.", CYAN))
            time.sleep(1)
        elif choice == '5':
            break
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)

def settings_screen():
    set_windows_ansi()
    while True:
        clear()
        print(color_text("=== NOVIUM SETTINGS ===", BOLD + CYAN))
        print()
        print(color_text("1) Create Desktop Shortcut", BLUE))
        print(color_text("2) Enable Autostart", BLUE))
        print(color_text("3) Hard Reset", YELLOW))
        print(color_text("4) Manage Features (Toggles)", CYAN))
        print(color_text("5) Back", MAGENTA))
        print()
        choice = input(color_text("Select > ", GREEN)).strip()
        if choice == '1':
            clear()
            create_desktop_launcher()
            input(color_text('Press Enter to return to Settings...', CYAN))
        elif choice == '2':
            clear()
            enable_autostart()
            input(color_text('Press Enter to return to Settings...', CYAN))
        elif choice == '3':
            clear()
            hard_reset()
            input(color_text('Press Enter to return to Settings...', CYAN))
        elif choice == '4':
            manage_features()
        elif choice == '5':
            return
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)

def setup_screen():
    set_windows_ansi()
    while True:
        clear()
        print(color_text("=== NOVIUM FIRST-RUN SETUP ===", BOLD + CYAN))
        print()
        print(color_text("Choose what you'd like to enable before you start:", BLUE))
        print(color_text("1) Create Desktop Shortcut", BLUE))
        print(color_text("2) Enable Autostart", BLUE))
        print(color_text("3) Customize logo color", MAGENTA))
        print(color_text("4) Manage Core Features (Toggles)", YELLOW))
        print(color_text("5) Finish setup", CYAN))
        print()
        choice = input(color_text("Select > ", GREEN)).strip()
        if choice == '1':
            clear()
            create_desktop_launcher()
            input(color_text('Press Enter to return to setup...', CYAN))
        elif choice == '2':
            clear()
            enable_autostart()
            input(color_text('Press Enter to return to setup...', CYAN))
        elif choice == '3':
            clear()
            customize_experience()
        elif choice == '4':
            manage_features()
        elif choice == '5':
            break
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)

# -----------------------
# SHELL & UI
# -----------------------
def splash_screen():
    set_windows_ansi()
    clear()
    logo_lines = color_logo(FULL_LOGO).splitlines()
    for line in logo_lines:
        print(line)
        time.sleep(0.01) # Beschleunigt für besseres Erlebnis
    print()
    print(color_text('Welcome to Novium', CYAN))
    for seconds in range(3, 0, -1):
        print(color_text(f'Starting in {seconds}...', YELLOW), end='\r', flush=True)
        time.sleep(1)
    print(' ' * shutil.get_terminal_size().columns, end='\r')

def system_detection_screen():
    set_windows_ansi()
    if Console:
        console = Console()
        console.print(color_logo(FULL_LOGO))
        console.print("\n[bold cyan]Welcome to Novium. Checking your environment now.[/bold cyan]\n")
    else:
        print(color_logo(FULL_LOGO))
        print(color_text("\nWelcome to Novium. Checking your environment now.\n", CYAN))
    
    checks = [
        ('psutil', lambda: psutil is not None),
        ('Web browser', check_browser_installed),
    ]
    results = {}
    
    for name, fn in checks:
        if Console:
            console.print(f"[bold blue]Looking for {name}...[/bold blue]", end='', style="dim")
        else:
            print(color_text(f"Looking for {name}...", BLUE), end='')
            
        time.sleep(0.6)
        found = fn()
        results[name] = found
        
        if Console:
            status = "[bold green]FOUND[/bold green]" if found else "[bold red]MISSING[/bold red]"
            console.print(status)
        else:
            status = color_text("FOUND", GREEN) if found else color_text("MISSING", RED)
            print(status)
            
    print()
    if Console:
        if all(results.values()):
            console.print("[bold green]All required components were found.[/bold green]")
        else:
            console.print("[bold yellow]Some components are missing. Novium may still run with limited features.[/bold yellow]")
    else:
        print(color_text("Dependencies check complete.", CYAN))
        
    print()
    input("Press Enter to continue...")
    return results

def show_shell_help():
    print(color_text('Novium built-in commands:', BOLD + CYAN))
    print(color_text('  help    - show this help text', BLUE))
    print(color_text('  stats   - display current system stats', BLUE))
    print(color_text('  settings- open Novium settings', BLUE))
    print(color_text('  setup   - rerun first-run setup options', BLUE))
    print(color_text('  sysinfo - display detailed system information', BLUE))
    print(color_text('  clear   - clear the screen', BLUE))
    print(color_text('  exit    - quit Novium', BLUE))
    print()
    input(color_text('Press Enter to continue...', CYAN))

def print_system_info():
    hw = detect_hardware()
    if Console:
        console = Console()
        console.rule("[bold magenta]System Information[/bold magenta]")
        console.print(f"OS: {platform.system()} {platform.release()}")
        console.print(f"Platform: {platform.platform()}")
        console.print(f"CPU cores: {hw.get('cpu_count', 'N/A')}")
        console.print(f"Memory: {hw.get('total_mem_gb', 'N/A')} GB")
        console.print(f"Disk free: {hw.get('disk_free_gb', 'N/A')} GB")
        console.print(f"Temperature: {get_temperature()}")
        console.print(f"Fan: {get_fan_rpm()}")
    else:
        print(color_text("=== System Information ===", MAGENTA))
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"CPU cores: {hw.get('cpu_count', 'N/A')}")
        print(f"Memory: {hw.get('total_mem_gb', 'N/A')} GB")
    print()
    input(color_text('Press Enter to continue...', CYAN))

def read_key(timeout=0.1):
    if os.name == 'nt':
        try:
            import msvcrt
            end = time.time() + timeout
            while time.time() < end:
                if msvcrt.kbhit():
                    return msvcrt.getwch()
                time.sleep(0.01)
        except Exception:
            return None
    else:
        import select
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            rlist, _, _ = select.select([fd], [], [], timeout)
            if rlist:
                return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return None

GENERAL_COMMANDS = ['help', 'stats', 'settings', 'setup', 'sysinfo', 'clear', 'exit']
def get_shell_hints():
    if os.name == 'nt':
        return ['dir', 'cls', 'ipconfig', 'tasklist', 'systeminfo']
    return ['ls', 'clear', 'uname -a', 'top', 'df -h', 'ip a', 'ps aux']

def render_shell(stats_dict, hints, last_output):
    set_windows_ansi()
    clear()
    left_lines = color_logo(N_LOGO).splitlines()
    stats_lines = [f"{k}: {v}" for k,v in stats_dict.items()]
    
    left_width = max(len(line) for line in left_lines) + 4
    max_lines = max(len(left_lines), max(len(stats_lines), len(hints) + 2))
    
    for i in range(max_lines):
        left = left_lines[i] if i < len(left_lines) else ""
        right = stats_lines[i] if i < len(stats_lines) else ""
        print(left.ljust(left_width) + right)
        
    print()
    print(color_text('Novium shell commands: ' + ', '.join(GENERAL_COMMANDS), CYAN))
    print(color_text('OS hints: ' + ', '.join(hints), YELLOW))
    print(color_text('Type a normal shell command to execute it.', BLUE))
    print()
    
    if last_output:
        for line in last_output:
            print(line)
        print()

def start_screen():
    config = load_config()
    last_output = []
    hints = get_shell_hints()
    input_buffer = ''
    stats = get_system_stats_snapshot()
    
    render_shell(stats, hints, last_output)
    print(color_text('novium> ', GREEN), end='', flush=True)
    
    last_refresh = time.time()
    
    while True:
        now = time.time()
        # Hinweis: Das Neuladen des Dashboards in-place kann flackern.
        if now - last_refresh >= 5.0: # Erhöht auf 5s, um ständige Interrupts zu mindern
            last_refresh = now
            
        key = read_key(0.1)
        if key is None:
            continue
            
        if key in ('\r', '\n'):
            command = input_buffer.strip()
            input_buffer = ''
            
            if not command:
                print('\n' + color_text('novium> ', GREEN), end='', flush=True)
                continue
            
            parts = command.lower().split()
            
            if command.lower() in ('exit', 'quit'):
                return 'exit'
            elif command.lower() == 'help':
                clear()
                show_shell_help()
                last_output = []
            elif command.lower() == 'stats':
                last_output = [f"{k}: {v}" for k,v in get_system_stats_snapshot().items()]
            elif command.lower() == 'settings':
                settings_screen()
            elif command.lower() == 'setup':
                setup_screen()
            elif command.lower() == 'sysinfo':
                print_system_info()
            elif command.lower() == 'clear':
                last_output = []
            elif command.lower().startswith('web '):
                query = " ".join(parts[1:])
                last_output = web_search(query)
            elif parts[0] == 'app' and len(parts) > 1:
                last_output = launch_app(command[4:])
            else:
                os.system(command)
                last_output = []
                
            render_shell(get_system_stats_snapshot(), hints, last_output)
            print(color_text('novium> ', GREEN), end='', flush=True)
            continue
            
        if key in ('\x08', '\x7f'):
            if input_buffer:
                input_buffer = input_buffer[:-1]
                print('\b \b', end='', flush=True)
            continue
            
        if key == '\x03': # Ctrl+C
            return 'exit'
            
        if len(key) == 1 and key.isprintable():
            input_buffer += key
            print(key, end='', flush=True)
            continue

# -----------------------
# MAIN ENTRY POINT
# -----------------------
if __name__ == "__main__":
    ensure_dependencies()
    if not MARKER_FILE.exists():
        system_detection_screen()
        setup_screen()
        MARKER_FILE.touch()
    else:
        splash_screen()
    
    start_screen()
    clear()
    print(color_text("Goodbye!", CYAN))