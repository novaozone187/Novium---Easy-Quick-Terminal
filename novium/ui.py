# ui.py - UI rendering helpers for Novium

import os
import shutil
import time
import subprocess

from utils import color_text, BOLD, BLUE, GREEN, CYAN, YELLOW, RED, MAGENTA, clear, set_windows_ansi
from system_monitor import get_temperature_sensors, get_fan_sensors

# Font manager integration
try:
    from core.font_manager import get_font_path, get_font_name
    FONT_SUPPORTED = True
except ImportError:
    FONT_SUPPORTED = False
    get_font_path = lambda: None
    get_font_name = lambda: 'default'


def get_font_config():
    """Returns current font configuration."""
    if not FONT_SUPPORTED:
        return None
    return {
        'name': get_font_name(),
        'path': get_font_path()
    }

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
    """Renders the main shell home screen with logo."""
    set_windows_ansi()
    clear()

    from config_manager import load_config
    config = load_config()
    logo_mode = config.get('logo_mode', 'novium')

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

    if logo_mode == 'os':
        # Run fastfetch to display OS logo and info
        try:
            subprocess.run(['fastfetch'], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(color_text("fastfetch not found. Run 'ff' to install it.", YELLOW))
        print()
    elif logo_mode == 'none':
        pass
    else:
        # logo_mode == 'novium'
        logo_color_name = config.get('logo_color', 'BLUE')
        color_mapping = {'BLUE': BLUE, 'CYAN': CYAN, 'MAGENTA': MAGENTA, 'GREEN': GREEN, 'YELLOW': YELLOW, 'RED': RED}
        logo_color = color_mapping.get(logo_color_name)
        display_logo(N_LOGO, color=logo_color, delay=0.002)
        print()

    # Print output from last command
    if last_output:
        for line in last_output:
            print(line)
        print()

    # Show stats if provided
    if stats:
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

    # Show reminder about help command
    print(color_text("Tip: Type 'help' to see all Novium commands.", BLUE))
    print()


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
            _manage_feature_toggles()
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
            _manage_feature_toggles()
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
                color_code = {'BLUE': BLUE, 'CYAN': CYAN, 'MAGENTA': MAGENTA, 'GREEN': GREEN, 'YELLOW': YELLOW, 'RED': RED}[name]
                print(color_text(f'{key}) {name}{selected}', color_code))
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


def _manage_feature_toggles():
    """Interactive feature toggle menu."""
    from config_manager import load_config, save_config
    config = load_config()
    while True:
        clear()
        print(color_text("=== FEATURE TOGGLES ===", BOLD + CYAN))
        print()
        print(f"  1) Hardware Monitoring: {color_text('Enabled' if config['hardware_monitoring'] else 'Disabled', GREEN if config['hardware_monitoring'] else RED)}")
        print(f"  2) Web Search:          {color_text('Enabled' if config['web_search_enabled'] else 'Disabled', GREEN if config['web_search_enabled'] else RED)}")
        print(f"  3) App Launcher:        {color_text('Enabled' if config['app_launcher_active'] else 'Disabled', GREEN if config['app_launcher_active'] else RED)}")
        print(f"  4) Autostart:           {color_text('Enabled' if config['autostart_enabled'] else 'Disabled', GREEN if config['autostart_enabled'] else RED)}")
        print(f"  5) Logo Mode:           {color_text(config.get('logo_mode', 'novium'), CYAN)}")
        print()
        print(color_text("Select a number to toggle, or 0 to go back:", BLUE))
        toggle_choice = input(color_text("Select > ", GREEN)).strip()
        if toggle_choice == '1':
            config['hardware_monitoring'] = not config['hardware_monitoring']
            save_config(config)
            status = 'Enabled' if config['hardware_monitoring'] else 'Disabled'
            print(color_text(f"Hardware Monitoring: {status}.", GREEN))
            time.sleep(1)
        elif toggle_choice == '2':
            config['web_search_enabled'] = not config['web_search_enabled']
            save_config(config)
            status = 'Enabled' if config['web_search_enabled'] else 'Disabled'
            print(color_text(f"Web Search: {status}.", GREEN))
            time.sleep(1)
        elif toggle_choice == '3':
            config['app_launcher_active'] = not config['app_launcher_active']
            save_config(config)
            status = 'Enabled' if config['app_launcher_active'] else 'Disabled'
            print(color_text(f"App Launcher: {status}.", GREEN))
            time.sleep(1)
        elif toggle_choice == '4':
            config['autostart_enabled'] = not config['autostart_enabled']
            save_config(config)
            status = 'Enabled' if config['autostart_enabled'] else 'Disabled'
            print(color_text(f"Autostart: {status}.", GREEN))
            time.sleep(1)
        elif toggle_choice == '5':
            print(color_text("Choose logo mode:", BLUE))
            print(color_text("  1) Novium  2) OS (fastfetch)  3) None", CYAN))
            logo_choice = input(color_text("Select > ", GREEN)).strip()
            if logo_choice == '1':
                config['logo_mode'] = 'novium'
            elif logo_choice == '2':
                config['logo_mode'] = 'os'
            elif logo_choice == '3':
                config['logo_mode'] = 'none'
            save_config(config)
            print(color_text(f"Logo Mode set to {config['logo_mode']}.", GREEN))
            time.sleep(1)
        elif toggle_choice == '0':
            break
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)
