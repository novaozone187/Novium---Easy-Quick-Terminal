# ui.py - UI rendering helpers for Novium

import os
import sys
import shutil
import time
import subprocess

from utils import color_text, BOLD, BLUE, GREEN, CYAN, YELLOW, RED, MAGENTA, clear, set_windows_ansi, read_key, draw_box
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





def render_sensor_screen():
    """Renders the fan/temperature sensor screen."""
    clear()
    draw_header("SENSOR STATUS", border_color=CYAN)
    print()

    fans = get_fan_sensors()
    temps = get_temperature_sensors()

    if fans:
        lines = [f"  {label}: {color_text(value, GREEN)}" for label, value in fans]
        draw_box(lines, title="FAN SENSORS", border_color=CYAN)
    else:
        print(color_text("  No fan sensors available.", YELLOW))

    print()

    if temps:
        lines = [f"  {label}: {color_text(value, GREEN)}" for label, value in temps]
        draw_box(lines, title="TEMPERATURE SENSORS", border_color=CYAN)
    else:
        print(color_text("  No temperature sensors available.", YELLOW))

    print()
    input(color_text("Press Enter to continue...", BLUE))


def render_settings_screen():
    """Renders the settings menu."""
    set_windows_ansi()
    while True:
        clear()
        draw_box([
            "  1) Create Desktop Shortcut",
            "  2) Enable Autostart",
            "  3) Hard Reset",
            "  4) Manage Features (Toggles)",
            "  5) Novium Network",
            "  6) Back",
        ], title="NOVIUM SETTINGS", border_color=CYAN)
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
            clear()
            _network_settings()
        elif choice == '6':
            return
        else:
            print(color_text('Invalid option', RED))
            time.sleep(1)


def render_setup_screen():
    """Renders the first-run setup screen."""
    set_windows_ansi()
    while True:
        clear()
        draw_box([
            "  1) Create Desktop Shortcut",
            "  2) Enable Autostart",
            "  3) Customize logo color",
            "  4) Manage Core Features (Toggles)",
            "  5) Finish setup",
        ], title="FIRST-RUN SETUP", border_color=CYAN)
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
    color_map = {'BLUE': BLUE, 'CYAN': CYAN, 'MAGENTA': MAGENTA, 'GREEN': GREEN, 'YELLOW': YELLOW, 'RED': RED}
    options = ['BLUE', 'CYAN', 'MAGENTA', 'GREEN', 'YELLOW', 'RED', 'Skip']
    while True:
        clear()
        lines = []
        for i, name in enumerate(options, 1):
            marker = " (current)" if name == current else ""
            c = color_map.get(name, BLUE) if name != 'Skip' else BLUE
            lines.append(color_text(f"  {i}) {name}{marker}", c))
        draw_box(lines, title="CUSTOMIZE LOGO COLOR", border_color=CYAN)
        choice = input(color_text('Select > ', GREEN)).strip()
        if choice == '7' or (choice.isdigit() and int(choice) == len(options)):
            break
        mapping = {str(i): name for i, name in enumerate(options, 1) if name != 'Skip'}
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
        lines = [
            f"  1) Hardware Monitoring: {color_text('Enabled' if config['hardware_monitoring'] else 'Disabled', GREEN if config['hardware_monitoring'] else RED)}",
            f"  2) Web Search:          {color_text('Enabled' if config['web_search_enabled'] else 'Disabled', GREEN if config['web_search_enabled'] else RED)}",
            f"  3) App Launcher:        {color_text('Enabled' if config['app_launcher_active'] else 'Disabled', GREEN if config['app_launcher_active'] else RED)}",
            f"  4) Autostart:           {color_text('Enabled' if config['autostart_enabled'] else 'Disabled', GREEN if config['autostart_enabled'] else RED)}",
            f"  5) Logo Mode:           {color_text(config.get('logo_mode', 'novium'), CYAN)}",
            "",
            "  0) Back",
        ]
        draw_box(lines, title="FEATURE TOGGLES", border_color=CYAN)
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


def _network_connection_screen(net, url):
    set_windows_ansi()

    cols = shutil.get_terminal_size().columns
    HOME = "\033[H"
    CLEAR_END = "\033[J"

    def _draw(lines, clear_first=True):
        content = "\n".join(lines)
        sys.stdout.write(HOME)
        if clear_first:
            sys.stdout.write(CLEAR_END)
            sys.stdout.write(HOME)
        sys.stdout.write(content)
        sys.stdout.write(CLEAR_END)
        sys.stdout.flush()

    def _network_box(body_lines):
        lines = []
        lines.append(color_text("╔" + "═" * (cols - 2) + "╗", CYAN))
        lines.append(color_text("║" + "NOVIUM NETWORK CONNECTION".center(cols - 2) + "║", BOLD + CYAN))
        lines.append(color_text("╚" + "═" * (cols - 2) + "╝", CYAN))
        lines.append("")
        lines.append(f"  Server: {color_text(url, GREEN)}")
        lines.append("")
        lines.append(color_text("  ── Progress ──", BOLD))
        lines.extend(body_lines)
        return lines

    # ── Phase 1: Connecting ──
    _draw(_network_box([
        color_text("  Connecting...", YELLOW),
        "",
        color_text("  [Q] Cancel", YELLOW),
    ]), clear_first=True)

    ok, msg = net.connect(url)
    if not ok:
        _draw(_network_box([
            color_text(f"  Connection failed", RED),
            f"  {color_text(msg, RED)}",
            "",
            color_text("  Press Enter to return...", CYAN),
        ]), clear_first=True)
        input()
        return

    # ── Phase 2: Poll loop ──
    got_welcome = False
    code = None
    code_shown = False
    cancelled = False
    spinner = "|/-\\"
    spin_idx = 0

    while not net.verified:
        key = read_key(timeout=0.3)
        if key and key.lower() == 'q':
            cancelled = True
            break

        if net._welcome_received and not got_welcome:
            got_welcome = True
        if net._pending_code and not code_shown:
            code = net._pending_code
            code_shown = True
        if not net.connected:
            _draw(_network_box([
                color_text("  Connection lost", RED),
                "",
                color_text("  Press Enter to return...", CYAN),
            ]), clear_first=True)
            input()
            return

        lines = []
        spin = spinner[spin_idx % len(spinner)]
        spin_idx += 1
        lines.append(color_text(f"  {spin} Connected to server", GREEN))
        if got_welcome:
            lines.append(color_text(f"  {spin} Package exchange verified", GREEN))
            lines.append(color_text(f"  {spin} Temp ID: {net.temp_id}", GREEN))
        if not code_shown:
            lines.append(color_text(f"  {spin} Awaiting verification in Discord...", YELLOW))
        else:
            lines.append(color_text(f"  {spin} Verification code received", CYAN))
            lines.append(color_text(f"  {spin} Awaiting confirmation in Discord...", YELLOW))
        lines.append("")
        if code_shown and code:
            code_display = "  ".join(code)
            lines.append(color_text(f"  Code: {code_display}", BOLD + MAGENTA))
            lines.append(color_text("  Open Discord -> /confirm", CYAN))
            lines.append(color_text("  Expires in 5 min", YELLOW))
        lines.append(color_text("  [Q] Cancel connection", YELLOW))
        _draw(_network_box(lines), clear_first=False)

    if cancelled:
        clear()
        reason = input(color_text("  Reason for disconnecting: ", GREEN)).strip() or "User cancelled connection screen"
        net.disconnect_with_reason(reason)
        return

    # ── Phase 3: Verified screen ──
    _draw(_network_box([
        color_text("  Connected to server", GREEN),
        color_text("  Package exchange verified", GREEN),
        color_text(f"  Temp ID: {net.temp_id}", GREEN),
        color_text("  Verification code received", GREEN),
        color_text("  Verification confirmed", GREEN),
        color_text(f"  VERIFIED as {net.client_id or 'NOVIUM-???'}", BOLD + GREEN),
        "",
        color_text("  You are now verified on the Novium Network!", BOLD + GREEN),
        "",
        color_text("  Press Enter to return to Novium...", CYAN),
    ]), clear_first=True)
    input()

def _network_settings():
    from config_manager import load_config, save_config
    from network import get_network
    config = load_config()
    net = get_network()
    while True:
        clear()
        current_url = config.get("network", {}).get("server_url", "ws://novium-network.duckdns.org:8765")
        auto = config.get("network", {}).get("enabled", False)

        info_lines = [
            f"  Status:       {color_text(net.status_text(), CYAN)}",
            f"  Server URL:   {color_text(current_url, GREEN)}",
            f"  Auto-connect: {color_text('ON' if auto else 'OFF', GREEN if auto else RED)}",
        ]
        if net.connected:
            info_lines.append(f"  Temp ID:      {color_text(net.temp_id, YELLOW)}")
            if net.client_id:
                info_lines.append(f"  Client ID:    {color_text(net.client_id, BOLD + GREEN)}")
        draw_box(info_lines, title="NOVIUM NETWORK", border_color=CYAN)

        menu_lines = [
            "  1) " + ("Disconnect" if net.connected else "Connect"),
            "  2) Change Server URL",
            "  3) Toggle Auto-Connect",
            "  4) Back",
        ]
        draw_box(menu_lines, border_color=CYAN)
        choice = input(color_text("  Select > ", GREEN)).strip()
        if choice == '1':
            if net.connected:
                print(color_text("  Why are you disconnecting? ", CYAN))
                reason = input(color_text("  Reason: ", GREEN)).strip()
                if not reason:
                    reason = "User disconnected via network settings"
                net.disconnect_with_reason(reason)
                cfg = load_config()
                cfg.setdefault("network", {})["enabled"] = False
                save_config(cfg)
                print(color_text(f"  Disconnected. Reason logged.", YELLOW))
            else:
                _network_connection_screen(net, current_url)
                if net.connected:
                    cfg = load_config()
                    cfg.setdefault("network", {})["enabled"] = True
                    save_config(cfg)
            input(color_text('  Press Enter...', CYAN))
        elif choice == '2':
            print(color_text(f"  Current: {current_url}", CYAN))
            new_url = input(color_text("  New URL (leave empty to keep): ", GREEN)).strip()
            if new_url:
                config.setdefault("network", {})["server_url"] = new_url
                save_config(config)
                print(color_text(f"  URL set to {new_url}", GREEN))
            else:
                print(color_text("  URL unchanged.", YELLOW))
            input(color_text('  Press Enter...', CYAN))
        elif choice == '3':
            enabled = not auto
            config.setdefault("network", {})["enabled"] = enabled
            save_config(config)
            print(color_text(f"  Auto-connect {'ON' if enabled else 'OFF'}.", GREEN))
            input(color_text('  Press Enter...', CYAN))
        elif choice == '4':
            return
        else:
            print(color_text('  Invalid option', RED))
            time.sleep(1)


def render_initial_home():
    """Renders the home screen once at startup (logo + stats, no looping)."""
    set_windows_ansi()
    clear()

    from config_manager import load_config
    from system_monitor import get_system_stats_snapshot

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
        try:
            subprocess.run(['fastfetch'], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(color_text("fastfetch not found. Run 'ff' to install it.", YELLOW))
        print()
    elif logo_mode == 'none':
        pass
    else:
        logo_color_name = config.get('logo_color', 'BLUE')
        color_mapping = {'BLUE': BLUE, 'CYAN': CYAN, 'MAGENTA': MAGENTA, 'GREEN': GREEN, 'YELLOW': YELLOW, 'RED': RED}
        logo_color = color_mapping.get(logo_color_name)
        display_logo(N_LOGO, color=logo_color, delay=0.002)
        print()

    stats = get_system_stats_snapshot()
    if stats:
        lines = [f"  {k:<15}: {color_text(v, GREEN)}" for k, v in stats.items()]
        draw_box(lines, title="SYSTEM STATS", border_color=CYAN)
        print()

    print(color_text("Tip: Type 'help' to see all Novium commands.", BLUE))
