# utils.py - Utility functions for Novium

import os
import re
import shutil
import sys
import time
import ctypes


# --- ANSI Color Definitions ---
RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"

COLOR_THEMES = {
    "BLUE": BLUE,
    "CYAN": CYAN,
    "GREEN": GREEN,
    "YELLOW": YELLOW,
    "RED": RED,
    "MAGENTA": MAGENTA,
}


# --- Theme System ---

THEME = {
    "primary": BLUE,
    "secondary": CYAN,
    "accent": GREEN,
    "warning": YELLOW,
    "error": RED,
    "highlight": MAGENTA,
    "border": CYAN,
    "stat_label": BLUE,
    "stat_value": GREEN,
    "header": BOLD + CYAN,
    "success": GREEN,
    "neutral": BLUE,
}

_THEME_COLOR_MAP = {
    "BLUE": BLUE,
    "CYAN": CYAN,
    "MAGENTA": MAGENTA,
    "GREEN": GREEN,
    "YELLOW": YELLOW,
    "RED": RED,
}


def apply_theme(config):
    """Update THEME colors based on config's logo_color."""
    logo_c = _THEME_COLOR_MAP.get(config.get("logo_color", "BLUE"), BLUE)
    THEME["primary"] = logo_c
    THEME["border"] = logo_c
    THEME["header"] = BOLD + logo_c
    if logo_c == RED:
        THEME["secondary"] = MAGENTA
    elif logo_c == MAGENTA:
        THEME["secondary"] = CYAN
    elif logo_c == GREEN:
        THEME["secondary"] = CYAN
    else:
        THEME["secondary"] = CYAN


# --- ANSI-aware string helpers ---

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')


def visible_len(text):
    """Return visible length of a string (stripping ANSI codes)."""
    return len(_ANSI_RE.sub('', text))


def pad_to(text, width):
    """Pad text with spaces to reach given visible width."""
    vis = visible_len(text)
    if vis >= width:
        return text
    return text + ' ' * (width - vis)


# --- Box Drawing ---

def draw_box(lines, title=None, border_color=None):
    """Print a bordered box with content lines and optional title.

    Args:
        lines: List of strings (may contain ANSI color codes).
        title: Optional title string displayed in top border.
        border_color: ANSI color for border. Defaults to THEME['border'].
    """
    if border_color is None:
        border_color = THEME["border"]

    width = max((visible_len(l) for l in lines), default=0)
    if title:
        width = max(width, visible_len(title) + 4)
    term_w = shutil.get_terminal_size().columns - 2
    width = min(width + 4, term_w)
    width = max(width, 30)

    if title:
        pad = width - 6 - visible_len(title)
        if pad < 0:
            pad = 0
        print(color_text("╔═ " + title + " ═" + "═" * pad + "╗", border_color))
    else:
        print(color_text("╔" + "═" * (width - 2) + "╗", border_color))

    for line in lines:
        vis = visible_len(line)
        if vis <= width - 4:
            print(color_text("║ ", border_color) + line + " " * (width - 4 - vis) + color_text(" ║", border_color))
        else:
            print(color_text("║ ", border_color) + line + color_text(" ║", border_color))

    print(color_text("╚" + "═" * (width - 2) + "╝", border_color))


def draw_header(title, char="═", color=None):
    """Print a full-width separator with centered title."""
    if color is None:
        color = THEME["secondary"]
    cols = shutil.get_terminal_size().columns
    avail = cols - visible_len(title) - 2
    if avail > 0:
        left = avail // 2
        right = avail - left
        print(color_text(char * left + " " + title + " " + char * right, color))
    else:
        print(color_text(title, color))


def draw_table(headers, rows, border_color=None):
    """Print a formatted table with headers and rows.

    Args:
        headers: List of header label strings.
        rows: List of lists, each inner list is a row of cell values.
              Cell values may contain ANSI color codes.
        border_color: ANSI color for header/separator.
    """
    if border_color is None:
        border_color = THEME["border"]

    col_widths = []
    ncols = len(headers)
    for i in range(ncols):
        w = visible_len(str(headers[i]))
        for row in rows:
            if i < len(row):
                w = max(w, visible_len(str(row[i])))
        col_widths.append(w)

    # Scale down if too wide for terminal
    term_w = shutil.get_terminal_size().columns - 4
    total = sum(col_widths) + (ncols - 1) * 3 + 4
    if total > term_w:
        ratio = (term_w - 4 - (ncols - 1) * 3) / sum(col_widths)
        col_widths = [max(int(w * ratio), 5) for w in col_widths]

    def fmt_row(cells):
        parts = []
        for i, cell in enumerate(cells):
            if i < ncols:
                parts.append(pad_to(str(cell), col_widths[i]))
        return "   ".join(parts)

    # Header
    print(color_text(fmt_row(headers), BOLD + border_color))
    # Separator
    sep = "   ".join("─" * w for w in col_widths)
    print(color_text(sep, border_color))
    # Rows
    for row in rows:
        print(fmt_row(row))


# --- Status Bar ---

def render_status_bar(version="", connected=False, client_id=None, verified=False, cpu=None, mem=None):
    """Print a single-line status bar at the bottom of the terminal."""
    parts = []
    parts.append(color_text(f" Novium {version}", BOLD + THEME["primary"]))
    parts.append(color_text(" │ ", THEME["neutral"]))
    if connected:
        status_text = "CONNECTED"
        if verified and client_id:
            status_text += f" {client_id}"
        parts.append(color_text(status_text, THEME["success"]))
    else:
        parts.append(color_text("DISCONNECTED", THEME["warning"]))
    if cpu is not None:
        parts.append(color_text(" │ CPU ", THEME["neutral"]) + color_text(cpu, THEME["accent"]))
    if mem is not None:
        parts.append(color_text(" │ MEM ", THEME["neutral"]) + color_text(mem, THEME["accent"]))
    parts.append(color_text(" │", THEME["neutral"]))
    print("".join(parts))


def color_text(text, color=None):
    """Wraps text with ANSI color codes."""
    if color is None:
        color = THEME["primary"]
    return f"{color}{text}{RESET}"


def clear():
    """Clears the terminal screen based on OS."""
    os.system("cls" if os.name == "nt" else "clear")


def center_print(text: str):
    """Prints text centered in the console."""
    cols = shutil.get_terminal_size().columns
    for line in text.splitlines():
        pad = max(0, (cols - visible_len(line)) // 2)
        print(" " * pad + line)


def set_windows_ansi():
    """Enables ANSI escape codes on Windows."""
    if os.name != 'nt':
        return
    try:
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def read_key(timeout=0.1):
    """Reads a single keypress with timeout. Returns None if no key pressed."""
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


def cursor_move(row, col):
    """Moves cursor to position (row, col)."""
    print(f"\033[{row};{col}H", end='', flush=True)


def clear_line():
    """Clears from cursor to end of line."""
    print("\033[K", end='', flush=True)
