# ui.py - UI rendering helpers for Novium

import os
import shutil
import time

from utils import color_text, BOLD, BLUE, GREEN, CYAN, clear, set_windows_ansi
from system_monitor import get_temperature_sensors, get_fan_sensors

# --- Screen Utilities ---


def display_logo(logo_content, color=None, delay=0.002):
    """Displays a multi-line ASCII logo with character-by-character animation."""
    for line in logo_content.splitlines():
        for ch in line:
            if color:
                print(color_text(ch, color), end='', flush=True)
            else:
                print(ch, end='', flush=True)
            time.sleep(delay)
        print()


def render_shell(stats, hints, last_output):
    """Renders the main shell home screen with logo, stats, and hints."""
    set_windows_ansi()
    clear()

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

    left_lines = N_LOGO.strip().splitlines()
    left_width = max(len(line) for line in left_lines) + 4

    # Convert stats dict to list of lines for alignment
    stats_lines = []
    if isinstance(stats, dict):
        for key, value in stats.items():
            stats_lines.append(f"{key}: {value}")
    elif isinstance(stats, list):
        stats_lines = stats
    else:
        stats_lines = [str(stats)]

    max_lines = max(len(left_lines), max(len(stats_lines), len(hints) + 2))
    for i in range(max_lines):
        left = left_lines[i] if i < len(left_lines) else ""
        right = stats_lines[i] if i < len(stats_lines) else ""
        print(left.ljust(left_width) + right)

    print()
    GENERAL_COMMANDS = ['help', 'stats', 'fan', 'settings', 'setup', 'sysinfo', 'nhome', 'clear', 'exit']
    print(color_text('Novium shell commands: ' + ', '.join(GENERAL_COMMANDS), CYAN))
    print(color_text('OS hints: ' + ', '.join(hints), BLUE))
    print(color_text('Type a normal shell command to execute it too.', GREEN))
    print(color_text('Type nhome to return to the main shell home screen.', GREEN))
    print()


def update_stats_panel(stats_dict):
    """Updates the live stats panel inline."""
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
    left_lines = N_LOGO.strip().splitlines()
    left_width = max(len(line) for line in left_lines) + 4

    stats_lines = []
    for key, value in stats_dict.items():
        stats_lines.append(f"{key}: {value}")

    for row, line in enumerate(stats_lines, start=1):
        cursor_move(row, left_width + 1)
        clear_line()
        print(line, end='', flush=True)


def cursor_move(row, col):
    """Moves cursor to position (row, col)."""
    print(f"\033[{row};{col}H", end='', flush=True)


def clear_line():
    """Clears from cursor to end of line."""
    print("\033[K", end='', flush=True)


def render_sensor_screen():
    """Renders the fan/temperature sensor screen."""
    clear()
    print(color_text("=== SENSOR STATUS ===", BOLD + CYAN))
    print()

    fans = get_fan_sensors()
    temps = get_temperature_sensors()

    if fans:
        print(color_text("Fan sensors:", BOLD + BLUE))
        for label, value in fans:
            print(f"  {label}: {color_text(value, CYAN)}")
    else:
        print(color_text("No fan sensors available.", YELLOW))

    print()

    if temps:
        print(color_text("Temperature sensors:", BOLD + BLUE))
        for label, value in temps:
            print(f"  {label}: {color_text(value, CYAN)}")
    else:
        print(color_text("No temperature sensors available.", YELLOW))

    print()
    input(color_text("Press Enter to continue...", BLUE))


def render_settings_screen():
    """Renders the settings menu."""
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
            from config_manager import create_desktop_launcher
            create_desktop_launcher()
            input(color_text('Press Enter to return to Settings...', CYAN))
        elif choice == '2':
            clear()
            from config_manager import enable_autostart
            enable_autostart()
            input(color_text('Press Enter to return to Settings...', CYAN))
        elif choice == '3':
            clear()
            from config_manager import hard_reset
            hard_reset()
            print(color_text("Hard reset completed.", GREEN))
            input(color_text('Press Enter to return to Settings...', CYAN))
        elif choice == '4':
            clear()
            from config_manager import load_config, save_config
            config = load_config()
            print(color_text("=== FEATURE TOGGLES ===", BOLD + CYAN))
            print()
            print(f"  Hardware Monitoring: {color_text('Enabled' if config['hardware_monitoring'] else 'Disabled', GREEN if config['hardware_monitoring'] else RED)}")
            print(f"  Web Search:          {color_text('Enabled' if config['web_search_enabled'] else 'Disabled', GREEN if config['web_search_enabled'] else RED)}")
            print(f"  App Launcher:        {color_text('Enabled' if config['app_launcher_active'] else 'Disabled', GREEN if config['app_launcher_active'] else RED)}")
            print(f"  Autostart:           {color_text('Enabled' if config['autostart_enabled'] else 'Disabled', GREEN if config['autostart_enabled'] else RED)}")
            print()
            print(color_text("To toggle, edit config.json directly.", BLUE))
            input(color_text('Press Enter to continue...', CYAN))
        elif choice == '5':
            return
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)


def render_setup_screen():
    """Renders the first-run setup screen."""
    set_windows_ansi()
    while True:
        clear()
        print(color_text("=== NOVIUM FIRST-RUN SETUP ===", BOLD + CYAN))
        print()
        print(color_text("Choose what you'd like to enable:", BLUE))
        print(color_text("1) Create Desktop Shortcut", BLUE))
        print(color_text("2) Enable Autostart", BLUE))
        print(color_text("3) Customize logo color", MAGENTA))
        print(color_text("4) Manage Core Features (Toggles)", YELLOW))
        print(color_text("5) Finish setup", CYAN))
        print()
        choice = input(color_text("Select > ", GREEN)).strip()
        if choice == '1':
            clear()
            from config_manager import create_desktop_launcher
            create_desktop_launcher()
            input(color_text('Press Enter to return to setup...', CYAN))
        elif choice == '2':
            clear()
            from config_manager import enable_autostart
            enable_autostart()
            input(color_text('Press Enter to return to setup...', CYAN))
        elif choice == '3':
            clear()
            _customize_logo_color()
            input(color_text('Press Enter to return to setup...', CYAN))
        elif choice == '4':
            clear()
            from config_manager import load_config, save_config
            config = load_config()
            print(color_text("=== FEATURE TOGGLES ===", BOLD + CYAN))
            print()
            print(f"  Hardware Monitoring: {color_text('Enabled' if config['hardware_monitoring'] else 'Disabled', GREEN if config['hardware_monitoring'] else RED)}")
            print(f"  Web Search:          {color_text('Enabled' if config['web_search_enabled'] else 'Disabled', GREEN if config['web_search_enabled'] else RED)}")
            print(f"  App Launcher:        {color_text('Enabled' if config['app_launcher_active'] else 'Disabled', GREEN if config['app_launcher_active'] else RED)}")
            print(f"  Autostart:           {color_text('Enabled' if config['autostart_enabled'] else 'Disabled', GREEN if config['autostart_enabled'] else RED)}")
            print()
            print(color_text("To toggle, edit config.json directly.", BLUE))
            input(color_text('Press Enter to continue...', CYAN))
        elif choice == '5':
            # Mark setup as complete
            from config_manager import MARKER_FILE
            MARKER_FILE.touch()
            break
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)


def _customize_logo_color():
    """Lets user pick a logo color."""
    from config_manager import load_config, save_config
    config = load_config()
    current = config.get('logo_color', 'BLUE')
    options = [
        ('1', 'BLUE'),
        ('2', 'CYAN'),
        ('3', 'MAGENTA'),
        ('4', 'GREEN'),
        ('5', 'YELLOW'),
        ('6', 'RED'),
        ('7', 'Skip'),
    ]
    while True:
        clear()
        print(color_text('=== CUSTOMIZE LOGO COLOR ===', BOLD + CYAN))
        print()
        for key, name in options:
            if name == 'Skip':
                print(color_text(f'{key}) {name}', BLUE))
            else:
                selected = ' (current)' if current == name else ''
                print(color_text(f'{key}) {name}{selected}', color_text('', name)))
        print()
        choice = input(color_text('Select > ', GREEN)).strip()
        if choice == '7':
            break
        mapping = {opt[0]: opt[1] for opt in options if opt[1] != 'Skip'}
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
