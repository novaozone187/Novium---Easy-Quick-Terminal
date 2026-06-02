"""
install.py - Linux-safe dependency installer for Novium.

Detects the operating system and Linux distribution, then installs
dependencies using the appropriate package manager or virtual environment.

Usage:
    python3 install.py

This script is safe to run on:
- Windows (uses pip directly)
- macOS (uses pip directly)
- Linux (detects distro, handles PEP 668 externally-managed-environment)
"""

import sys
import subprocess
import os
import platform
from pathlib import Path


def detect_linux_distro():
    """Detects the Linux distribution name from /etc/os-release."""
    if os.name != 'posix':
        return None
    
    os_release = Path('/etc/os-release')
    if os_release.exists():
        try:
            data = os_release.read_text(encoding='utf-8')
            for line in data.splitlines():
                if line.startswith('ID='):
                    return line.split('=', 1)[1].strip().strip('"').lower()
        except Exception:
            pass
    return None


def is_externally_managed():
    """Checks if the current Python environment is externally managed (PEP 668)."""
    try:
        sysconfig = __import__('sysconfig')
        paths = sysconfig.get_paths()
        scheme = sysconfig.get_default_scheme()
        
        # Check for PEP 668 marker file
        if os.name == 'posix':
            # Common locations for externally-managed-environment marker
            marker_paths = [
                '/usr/lib/python3/dist-packagesEXTERNALLY-MANAGED',
                '/usr/lib64/python3/dist-packagesEXTERNALLY-MANAGED',
            ]
            # Also check sysconfig paths
            for key in ('purelib', 'platlib', 'data'):
                if key in paths:
                    marker = os.path.join(paths[key], 'EXTERNALLY-MANAGED')
                    if os.path.exists(marker):
                        return True
    except Exception:
        pass
    
    # Also try running pip with --break-system-packages to see if it's blocked
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--dry-run', 'pip'],
            capture_output=True, text=True, timeout=10
        )
        if 'externally-managed-environment' in result.stderr.lower():
            return True
    except Exception:
        pass
    
    return False


def create_venv(venv_dir):
    """Creates a virtual environment at the specified directory."""
    if venv_dir.exists() and any(venv_dir.iterdir()):
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'venv', str(venv_dir)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return True
        else:
            print(f"[WARNING] Failed to create venv: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("[WARNING] Venv creation timed out.")
        return False
    except Exception as e:
        print(f"[WARNING] Venv creation failed: {e}")
        return False


def install_in_venv(venv_dir, requirements_file):
    """Installs dependencies in a virtual environment."""
    if os.name == 'nt':
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        pip_path = venv_dir / "bin" / "pip3"
        python_path = venv_dir / "bin" / "python3"
    
    # Bootstrap pip if needed
    if not pip_path.exists():
        try:
            result = subprocess.run(
                [str(python_path), '-m', 'ensurepip', '--default-pip'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                print("[WARNING] Failed to bootstrap pip in venv.")
                return False
        except Exception as e:
            print(f"[WARNING] Failed to bootstrap pip: {e}")
            return False
    
    # Install requirements
    try:
        result = subprocess.run(
            [str(pip_path), 'install', '-r', str(requirements_file)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return True
        else:
            print(f"[WARNING] Venv install failed: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("[WARNING] Venv install timed out.")
        return False
    except Exception as e:
        print(f"[WARNING] Venv install failed: {e}")
        return False


def get_linux_install_commands(distro):
    """Returns Linux-specific install commands for the detected distribution."""
    if distro in ('ubuntu', 'debian', 'linuxmint', 'pop', 'kali', 'raspbian'):
        return {
            'system': 'sudo apt update && sudo apt install -y python3-psutil',
            'pip': 'sudo apt install -y python3-pip && python3 -m pip install -r requirements.txt',
            'venv': 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt',
        }
    elif distro in ('fedora', 'rhel', 'centos', 'rocky', 'almalinux', 'amzn'):
        return {
            'system': 'sudo dnf install -y python3-psutil',
            'pip': 'sudo dnf install -y python3-pip && python3 -m pip install -r requirements.txt',
            'venv': 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt',
        }
    elif distro == 'arch':
        return {
            'system': 'sudo pacman -S python-psutil',
            'pip': 'sudo pacman -S python-pip && python3 -m pip install -r requirements.txt',
            'venv': 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt',
        }
    elif distro == 'alpine':
        return {
            'system': 'sudo apk add py3-psutil',
            'pip': 'sudo apk add py3-pip && python3 -m pip install -r requirements.txt',
            'venv': 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt',
        }
    elif distro == 'opensuse-tumbleweed' or distro == 'opensuse-leap':
        return {
            'system': 'sudo zypper install -y python3-psutil',
            'pip': 'sudo zypper install -y python3-pip && python3 -m pip install -r requirements.txt',
            'venv': 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt',
        }
    else:
        return {
            'system': 'apt install python3-psutil  (or equivalent for your distro)',
            'pip': 'apt install python3-pip && python3 -m pip install -r requirements.txt',
            'venv': 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt',
        }


def main():
    """Main installer logic."""
    here = Path(__file__).resolve().parent
    req = here / "requirements.txt"
    venv_dir = here / ".venv"
    
    if not req.exists():
        print("[ERROR] requirements.txt not found")
        return 1
    
    print("Installing Novium dependencies...")
    print()
    
    # Check if psutil is already installed
    try:
        import psutil
        print("[OK] psutil is already installed.")
        return 0
    except ImportError:
        pass
    
    # Check OS
    if os.name == 'nt':
        # Windows - pip should work directly
        print("Platform: Windows")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(req)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("[SUCCESS] All dependencies installed successfully.")
                return 0
            else:
                print(f"[ERROR] pip install failed: {result.stderr.strip()}")
                return 1
        except subprocess.TimeoutExpired:
            print("[ERROR] pip install timed out.")
            return 1
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return 1
    
    elif os.name == 'posix':
        if platform.system() == 'Darwin':
            # macOS - pip should work directly
            print("Platform: macOS")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', str(req)],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    print("[SUCCESS] All dependencies installed successfully.")
                    return 0
                else:
                    print(f"[ERROR] pip install failed: {result.stderr.strip()}")
                    return 1
            except subprocess.TimeoutExpired:
                print("[ERROR] pip install timed out.")
                return 1
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                return 1
        else:
            # Linux
            distro = detect_linux_distro()
            distro_name = distro if distro else "unknown"
            print(f"Platform: Linux (distro: {distro_name})")
            print()
            
            # Check if externally managed
            if is_externally_managed():
                print("[WARNING] Externally-managed Python environment detected (PEP 668).")
                print()
                print("Cannot install pip packages system-wide. Choose an option:")
                print()
                
                commands = get_linux_install_commands(distro)
                
                print("  1) Install system package (requires sudo):")
                print(f"     {commands['system']}")
                print()
                print("  2) Create virtual environment (recommended):")
                print(f"     {commands['venv']}")
                print()
                print("  3) Skip (dependencies must be installed manually)")
                print()
                
                choice = input("Select [1/2/3]: ").strip()
                
                if choice == '1':
                    print(f"\nRunning: {commands['system']}")
                    try:
                        result = subprocess.run(
                            commands['system'],
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        if result.returncode == 0:
                            print("[SUCCESS] System package installed.")
                            return 0
                        else:
                            print(f"[ERROR] System install failed: {result.stderr.strip()}")
                            return 1
                    except subprocess.TimeoutExpired:
                        print("[ERROR] System install timed out.")
                        return 1
                    except Exception as e:
                        print(f"[ERROR] System install failed: {e}")
                        return 1
                
                elif choice == '2':
                    print(f"\nCreating virtual environment at {venv_dir}...")
                    if create_venv(venv_dir):
                        print("Installing dependencies in virtual environment...")
                        if install_in_venv(venv_dir, req):
                            print("[SUCCESS] Dependencies installed in virtual environment.")
                            print(f"\nRun Novium with: {venv_dir / 'bin' / 'python3'} novium.py")
                            return 0
                        else:
                            print("[ERROR] Failed to install in virtual environment.")
                            return 1
                    else:
                        print("[ERROR] Failed to create virtual environment.")
                        return 1
                
                else:
                    print("\nSkipping automatic installation.")
                    print("Please install dependencies manually:")
                    print(f"  {commands['pip']}")
                    return 0
            
            else:
                # Not externally managed, pip should work
                print("pip environment is available.")
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '-r', str(req)],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0:
                        print("[SUCCESS] All dependencies installed successfully.")
                        return 0
                    else:
                        print(f"[ERROR] pip install failed: {result.stderr.strip()}")
                        return 1
                except subprocess.TimeoutExpired:
                    print("[ERROR] pip install timed out.")
                    return 1
                except Exception as e:
                    print(f"[ERROR] Unexpected error: {e}")
                    return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
