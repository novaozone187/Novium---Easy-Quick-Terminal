"""
Simple installer script for Novium dependencies.
Usage: python install.py
This will pip-install packages from requirements.txt into the current Python environment.
"""
import sys
import subprocess
import os

here = os.path.dirname(__file__)
req = os.path.join(here, "requirements.txt")

def main():
    if not os.path.exists(req):
        print("requirements.txt not found")
        return
    print("Installing dependencies from requirements.txt...")
    try:
        # Use subprocess.check_call for reliable error checking on installation failure
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req])
        print("\n[SUCCESS] All dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Dependency installation failed! Exit code: {e.returncode}")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()
