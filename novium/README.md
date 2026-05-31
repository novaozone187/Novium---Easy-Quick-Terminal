# Novium

Novium is a terminal-based app launcher and system dashboard for **Windows, macOS, and Linux**. It combines a friendly first-run setup experience with live system stats, shell command execution, fastfetch integration, and a customizable logo.

**Zero manual setup** — Novium auto-installs all dependencies on first launch.

## Features

- **Auto-installs dependencies** — `psutil` and other requirements are installed automatically on first run
- Animated splash screen with typing logo effect
- Live system stats panel (CPU, memory, disk, temperature, fan RPM, time)
- `fan` screen for detailed temperature and fan sensor monitoring
- **fastfetch integration** — auto-installs fastfetch and lets you switch to the OS logo
- **Logo switcher** — choose between Novium logo, OS logo (fastfetch), or no logo
- Built-in terminal shell with command hints per OS
- Web search (`web <query>`) opens Google in your browser
- App launcher (`app <name>`) for quick application lookup
- Color customization for the Novium logo
- Desktop shortcut and autostart setup
  - **Windows**: Creates a `.lnk` shortcut with an icon
  - **Linux**: Creates a `.desktop` file that opens a terminal with Novium
  - **macOS**: Creates a `.desktop` file compatible with desktop environments
- First-run wizard to configure everything before use
- Cross-platform: works on Windows, macOS, and Linux

## Install

### Prerequisites

- **Python 3.10 or higher** (check with `python3 --version`)
- **pip** (usually comes with Python; check with `python3 -m pip --version`)

If Python is not installed:

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip

# macOS
brew install python3

# Windows
# Download from https://www.python.org/downloads/ (check "Add to PATH" during install)
```

### Quick Start (No Manual Setup)

1. Clone the repository:

```bash
git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git
cd Novium---Easy-Quick-Terminal
```

2. Run Novium — it will auto-install `psutil` and all dependencies:

```bash
python3 novium.py
```

That's it. Novium handles everything else.

### Manual Install (Optional)

If you prefer to install dependencies manually:

```bash
python3 -m pip install -r requirements.txt
```

Then run:

```bash
python3 novium.py
```

### Windows Users

On Windows, use `python` instead of `python3`:

```bash
git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git
cd Novium---Easy-Quick-Terminal
python novium.py
```

## First-Run Setup

On first launch, Novium:

1. Shows an animated splash screen with logo
2. Detects your environment (Python version, OS, browsers, psutil, fastfetch)
3. Runs a setup wizard to configure:
   - Desktop shortcut creation
   - Autostart on login
   - Logo color (Blue, Cyan, Magenta, Green, Yellow, Red)
   - Feature toggles (hardware monitoring, web search, app launcher, autostart)
4. Saves your preferences to `config.json`

## Built-in Commands

| Command | Description |
|---------|-------------|
| `help` | Show built-in command help |
| `stats` | Display current system stats |
| `fan` | Show fan and temperature sensor status |
| `settings` | Open Novium settings menu |
| `setup` | Rerun first-run setup wizard |
| `sysinfo` | Display detailed system information |
| `nhome` | Return to the Novium home shell |
| `clear` | Clear the screen |
| `exit` | Quit Novium |
| `ff` | Run fastfetch (installs it if missing) |
| `logo` | Switch logo: Novium / OS / None |
| `web <query>` | Open Google search in your browser |
| `app <name>` | Launch or search for an application |
| `color <COLOR>` | Change logo color (BLUE, CYAN, MAGENTA, GREEN, YELLOW, RED) |
| `install fastfetch` | Manually install fastfetch |
| `nuke` | Completely remove Novium from your system |

Any other input is executed as a system command (`dir` on Windows, `ls` on Linux/macOS, etc.).

## Logo Modes

Novium supports three logo modes, configurable via the `logo` command or settings:

| Mode | Description |
|------|-------------|
| `novium` | Novium's ASCII logo with stats (default) |
| `os` | OS-specific logo via fastfetch |
| `none` | No logo, just the shell |

To switch: type `logo` in the Novium shell and choose your preference.

## fastfetch Integration

Novium can automatically install fastfetch on all platforms:

- **Windows**: Tries `winget`, `scoop`, then `choco`
- **macOS**: Uses `brew`
- **Linux**: Tries `apt`, `dnf`, `pacman`, `zypper`, `apk`

Run `ff` in the Novium shell to install or launch fastfetch.

## Configuration

All settings are stored in `config.json` in the working directory:

```json
{
  "logo_color": "BLUE",
  "logo_mode": "novium",
  "hardware_monitoring": true,
  "web_search_enabled": true,
  "app_launcher_active": false,
  "autostart_enabled": false
}
```

Edit this file directly to toggle features, or use the in-app settings menu.

## Requirements

- Python 3.10+
- No manual dependency installation required — Novium installs `psutil` automatically

## Troubleshooting

- **Dependencies not installing**: Ensure Python 3.10+ is installed and pip is available
- **No sensor data**: Your platform or `psutil` may not expose hardware sensors — this is normal on some systems
- **fastfetch not installing**: Try installing it manually via your system's package manager
- **Colors not showing on Windows**: Novium enables ANSI support automatically, but some older terminals may not support it

## Uninstalling

To completely remove Novium:

1. Type `nuke` in the Novium shell and confirm
2. Delete the Novium folder manually

This removes: setup marker, config.json, desktop shortcuts, autostart entries, and uninstalls `psutil`.

## License

This repository does not include a license file by default. Add one if you want to publish or share the project with explicit reuse terms.
