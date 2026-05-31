# utils.py - Utility functions for Novium

import os
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


def color_text(text, color=None):
    """Wraps text with ANSI color codes."""
    if color is None:
        color = BLUE
    return f"{color}{text}{RESET}"


def clear():
    """Clears the terminal screen based on OS."""
    os.system("cls" if os.name == "nt" else "clear")


def center_print(text: str):
    """Prints text centered in the console."""
    cols = shutil.get_terminal_size().columns
    for line in text.splitlines():
        pad = max(0, (cols - len(line)) // 2)
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
