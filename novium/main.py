# main.py - Entry point for the Novium application

import sys
from novium.novium import start_screen, set_windows_ansi # Assuming 'novium' module name is correct from structure

if __name__ == "__main__":
    try:
        set_windows_ansi()
        # Start the main shell loop
        start_screen()
    except Exception as e:
        print(f"\n[ERROR] An unrecoverable error occurred: {e}")