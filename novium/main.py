# main.py - Entry point for the Novium application

import sys
import os

# Ensure the script's directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novium import start_screen
from utils import set_windows_ansi

if __name__ == "__main__":
    try:
        set_windows_ansi()
        start_screen()
    except Exception as e:
        print(f"\n[ERROR] An unrecoverable error occurred: {e}")
        sys.exit(1)
