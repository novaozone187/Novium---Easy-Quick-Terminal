"""
config_manager.py - Re-exports config functions + self-removal (nuke) system.
"""

from config import *  # load_config, save_config, ensure_dependencies, MARKER_FILE, etc.

import os
import sys
import shutil
import subprocess
import platform
import tempfile
from pathlib import Path


def get_novium_dir():
    """Get the Novium installation directory."""
    return Path(__file__).resolve().parent.parent


def find_novium_processes():
    """Find all running Novium and related Python processes."""
    processes = []
    novium_dir = get_novium_dir()
    novium_dir_str = str(novium_dir)
    
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FI', 'IMAGENAME eq python3.exe', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    line = line.strip().strip('"')
                    if not line:
                        continue
                    parts = line.split('","')
                    if len(parts) >= 2:
                        pid = int(parts[0].strip('"'))
                        image = parts[1].strip('"')
                        # Check cmdline for novium reference
                        try:
                            cmdline_result = subprocess.run(
                                ['wmic', 'process', 'where', f'processid={pid}', 'get', 'commandline', '/VALUE'],
                                capture_output=True, text=True, timeout=5
                            )
                            if 'novium' in cmdline_result.stdout.lower() or novium_dir_str.lower() in cmdline_result.stdout.lower():
                                processes.append({'pid': pid, 'image': image, 'cmdline': cmdline_result.stdout})
                        except Exception:
                            pass
        else:
            result = subprocess.run(
                ['pgrep', '-f', 'novium', '-a'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        try:
                            pid = int(parts[0])
                            cmdline = parts[1]
                            processes.append({'pid': pid, 'cmdline': cmdline})
                        except ValueError:
                            pass
            
            # Also check for python processes with novium in cmdline
            result2 = subprocess.run(
                ['pgrep', '-f', 'python.*novium', '-a'],
                capture_output=True, text=True, timeout=10
            )
            if result2.returncode == 0:
                for line in result2.stdout.strip().splitlines():
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        try:
                            pid = int(parts[0])
                            if not any(p['pid'] == pid for p in processes):
                                cmdline = parts[1]
                                processes.append({'pid': pid, 'cmdline': cmdline})
                        except ValueError:
                            pass
    except Exception:
        pass
    
    return processes


def terminate_novium_processes():
    """Terminate all Novium-related processes."""
    processes = find_novium_processes()
    terminated = []
    
    for proc in processes:
        pid = proc['pid']
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True, timeout=5)
            else:
                subprocess.run(['kill', '-9', str(pid)], capture_output=True, timeout=5)
            terminated.append(pid)
        except Exception:
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True, timeout=10)
                else:
                    subprocess.run(['kill', '-9', str(pid)], capture_output=True, timeout=10)
                if pid not in terminated:
                    terminated.append(pid)
            except Exception:
                pass
    
    return terminated


def get_windows_startup_folder():
    """Get Windows startup folder path."""
    appdata = os.getenv('APPDATA')
    if appdata:
        return Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    return Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'


def get_desktop_folder():
    """Get user's desktop folder."""
    desktop = Path.home() / 'Desktop'
    if desktop.exists():
        return desktop
    return Path.home()


def collect_removal_targets():
    """Collect all files and directories that need to be removed."""
    novium_dir = get_novium_dir()
    targets = []
    
    # Novium directory itself
    targets.append(('directory', novium_dir))
    
    # Config files
    config_file = novium_dir / 'config.json'
    if config_file.exists():
        targets.append(('file', config_file))
    
    # Version file
    version_file = novium_dir / '.version'
    if version_file.exists():
        targets.append(('file', version_file))
    
    # Cache files
    pycache = novium_dir / '__pycache__'
    if pycache.exists():
        targets.append(('directory', pycache))
    
    # Core cache
    core_cache = novium_dir / 'core' / '__pycache__'
    if core_cache.exists():
        targets.append(('directory', core_cache))
    
    # Temp files
    novium_tmp = novium_dir / 'novium_tmp.txt'
    if novium_tmp.exists():
        targets.append(('file', novium_tmp))
    
    # Backup files
    novium_backup = novium_dir / '.novium_backup'
    if novium_backup.exists():
        targets.append(('directory', novium_backup))
    
    # Virtual environment
    venv_dir = novium_dir / '.venv'
    if venv_dir.exists():
        targets.append(('directory', venv_dir))
    
    # Desktop shortcuts
    desktop = get_desktop_folder()
    for name in ['Novium.lnk', 'run_novium.bat', 'Novium.desktop', 'novium-icon.svg']:
        f = desktop / name
        if f.exists():
            targets.append(('file', f))
    
    # Startup folder entries
    startup = get_windows_startup_folder()
    for name in ['run_novium.bat', 'Novium.lnk']:
        f = startup / name
        if f.exists():
            targets.append(('file', f))
    
    # Linux autostart entries
    linux_autostart = Path.home() / '.config' / 'autostart'
    for name in ['novium.desktop', 'novium-icon.svg']:
        f = linux_autostart / name
        if f.exists():
            targets.append(('file', f))
    
    # Setup marker
    marker = Path.home() / '.novium_setup_done'
    if marker.exists():
        targets.append(('file', marker))
    
    return targets


def create_windows_cleanup_script(novium_dir):
    """Create Windows cleanup script for self-deletion."""
    script_content = f'''@echo off
title Novium Cleanup
echo Removing Novium...

'''
    # Add file deletion commands
    for target_type, target_path in collect_removal_targets():
        if target_type == 'file':
            script_content += f'del /f /q "{target_path}" 2>nul\n'
        elif target_type == 'directory':
            script_content += f'rmdir /s /q "{target_path}" 2>nul\n'
    
    # Add removal of desktop/startup entries
    script_content += '''
rem Remove desktop shortcuts
del /f /q "%USERPROFILE%\\Desktop\\Novium.lnk" 2>nul
del /f /q "%USERPROFILE%\\Desktop\\run_novium.bat" 2>nul
del /f /q "%USERPROFILE%\\Desktop\\Novium.desktop" 2>nul
del /f /q "%USERPROFILE%\\Desktop\\novium-icon.svg" 2>nul

rem Remove startup entries
del /f /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\run_novium.bat" 2>nul
del /f /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\Novium.lnk" 2>nul

rem Remove autostart
del /f /q "%USERPROFILE%\\.config\\autostart\\novium.desktop" 2>nul
del /f /q "%USERPROFILE%\\.config\\autostart\\novium-icon.svg" 2>nul

rem Remove setup marker
del /f /q "%USERPROFILE%\\.novium_setup_done" 2>nul

rem Remove config
del /f /q "%CD%\\config.json" 2>nul
del /f /q "%CD%\\.version" 2>nul

rem Remove backup
rmdir /s /q "%CD%\\.novium_backup" 2>nul

rem Remove the novium directory itself
rmdir /s /q "%CD%" 2>nul

rem Delete this script
del /f /q "%%~f0"
'''
    return script_content


def create_linux_cleanup_script(novium_dir):
    """Create Linux cleanup script for self-deletion."""
    script_content = f'''#!/bin/bash
# Novium cleanup script
# Generated automatically - do not edit

echo "Removing Novium..."

'''
    # Add file/directory removal commands
    for target_type, target_path in collect_removal_targets():
        if target_type == 'file':
            script_content += f'rm -f "{target_path}"\n'
        elif target_type == 'directory':
            script_content += f'rm -rf "{target_path}"\n'
    
    # Add desktop/startup removal
    script_content += '''
# Remove desktop shortcuts
rm -f "$HOME/Desktop/Novium.lnk"
rm -f "$HOME/Desktop/run_novium.bat"
rm -f "$HOME/Desktop/Novium.desktop"
rm -f "$HOME/Desktop/novium-icon.svg"

# Remove startup entries
rm -f "$HOME/.config/autostart/novium.desktop"
rm -f "$HOME/.config/autostart/novium-icon.svg"

# Remove setup marker
rm -f "$HOME/.novium_setup_done"

# Remove config
rm -f "$HOME/Novium---Easy-Quick-Terminal/novium/config.json" 2>/dev/null
rm -f "$HOME/Novium---Easy-Quick-Terminal/novium/.version" 2>/dev/null

# Remove backup
rm -rf "$HOME/Novium---Easy-Quick-Terminal/novium/.novium_backup" 2>/dev/null

# Remove the novium directory
rm -rf "$0/.."

# Delete this script
rm -f "$0"
'''
    return script_content


def nuke_novium():
    """
    Completely remove Novium from the system.
    
    Returns:
        tuple: (removed_items, failed_items, terminated_pids)
    """
    removed = []
    failed = []
    terminated_pids = []
    
    # Step 1: Terminate all Novium processes
    print("Terminating Novium processes...")
    terminated_pids = terminate_novium_processes()
    if terminated_pids:
        removed.append(f"Terminated processes: {', '.join(str(p) for p in terminated_pids)}")
    else:
        removed.append("No running Novium processes found")
    
    # Step 2: Collect all removal targets
    targets = collect_removal_targets()
    
    # Step 3: Attempt direct removal
    for target_type, target_path in targets:
        try:
            if target_type == 'file':
                target_path.unlink()
                removed.append(str(target_path))
            elif target_type == 'directory':
                shutil.rmtree(str(target_path))
                removed.append(str(target_path))
        except Exception as e:
            failed.append(f"{target_path}: {str(e)}")
    
    # Step 4: Create cleanup script for remaining items
    novium_dir = get_novium_dir()
    cleanup_script = None
    
    if failed:
        try:
            if os.name == 'nt':
                script_content = create_windows_cleanup_script(novium_dir)
            else:
                script_content = create_linux_cleanup_script(novium_dir)
            
            cleanup_file = Path(tempfile.gettempdir()) / f"novium_cleanup_{os.getpid()}.{'bat' if os.name == 'nt' else 'sh'}"
            cleanup_file.write_text(script_content)
            cleanup_file.chmod(0o755)
            cleanup_script = str(cleanup_file)
        except Exception:
            pass
    
    return removed, failed, terminated_pids, cleanup_script


def execute_nuke():
    """Execute the full nuke operation with user confirmation."""
    print()
    print("=" * 60)
    print("  WARNING: NOVIUM SELF-REMOVAL")
    print("=" * 60)
    print()
    print("This will permanently remove Novium from this system.")
    print()
    print("The following will be deleted:")
    print("  - All Novium files and directories")
    print("  - Configuration files")
    print("  - Cache and temporary files")
    print("  - Desktop shortcuts and launchers")
    print("  - Startup/autostart entries")
    print("  - All running Novium processes")
    print()
    print("Type 'DELETE NOVIUM' to continue.")
    print("Any other input will cancel the operation.")
    print()
    
    confirm = input("Confirm: ").strip()
    
    if confirm != 'DELETE NOVIUM':
        print("Nuke cancelled.")
        return
    
    print()
    print("Executing nuke operation...")
    print()
    
    removed, failed, terminated_pids, cleanup_script = nuke_novium()
    
    if removed:
        print("Removed items:")
        for item in removed:
            print(f"  [OK] {item}")
    
    if failed:
        print()
        print("Failed to remove (will be cleaned by script):")
        for item in failed:
            print(f"  [!] {item}")
    
    # Execute cleanup script if created
    if cleanup_script:
        print()
        print(f"Running cleanup script: {cleanup_script}")
        try:
            if os.name == 'nt':
                subprocess.Popen([cleanup_script], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(['bash', cleanup_script])
        except Exception:
            print(f"Failed to execute cleanup script: {cleanup_script}")
    
    print()
    print("Novium has been removed from your system.")
    print()


if __name__ == '__main__':
    execute_nuke()
