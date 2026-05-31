# Novium

Novium is a terminal-based app launcher and system dashboard for Windows and POSIX systems. It combines a friendly first-run setup experience with live console stats, shell command execution, and optional hardware monitoring features.

Repository: https://github.com/novaozone187/Novium---Terminal-Based-App-launcher

## Features

- First-run splash with animated logo and environment detection
- Terminal shell with built-in commands and OS command hints
- Live stats panel for CPU, memory, disk, temperature, fan, and time
- `fan` monitor screen for available fan and temperature sensors
- Settings options for desktop shortcut and autostart
- Color customization for the Novium logo
- Support for running normal shell commands directly inside Novium

## Install

1. Clone the repository:

```bash
git clone https://github.com/novaozone187/Novium---Terminal-Based-App-launcher.git
cd Novium---Terminal-Based-App-launcher
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run Novium:

```bash
python novium.py
```

Alternatively, use the included installer script:

```bash
python install.py
```

## Built-in Commands

Available Novium commands:

- `help` — show built-in command help
- `stats` — display current system stats
- `fan` — show fan and temperature sensor status
- `settings` — open Novium settings
- `setup` — rerun first-run setup options
- `sysinfo` — display detailed system information
- `nhome` — return to the Novium home shell
- `clear` — clear the screen
- `exit` — quit Novium

Additional features:

- `color <COLOR>` — change the logo color to `BLUE`, `CYAN`, `MAGENTA`, `GREEN`, `YELLOW`, or `RED`
- Shell commands like `dir`, `ls`, `ipconfig`, `systeminfo`, and any normal OS command are supported

## First-run behavior

On first launch, Novium:

1. Shows a large styled logo and typing animation
2. Detects environment details like Python, OS, browser, and `psutil`
3. Provides setup options for shortcut creation, autostart, and logo color
4. Stores a marker file in the user home directory so first-run setup only appears once

## Notes

- `psutil` is required for hardware stats and sensor monitoring
- Novium performs a pre-launch dependency check and attempts to auto-install missing Python packages from `requirements.txt`
- Distro-specific command hints are provided for Linux systems, including Kali and Debian-based distros
- If `psutil` does not support `sensors_temperatures` or `sensors_fans` on your platform, Novium gracefully reports sensor data as unavailable
- Windows autostart and desktop shortcut creation are supported when running on Windows

## Troubleshooting

- If Novium fails to start, ensure Python 3.10+ is installed and `psutil` is available
- If fan or temperature monitoring reports no sensors, your platform or `psutil` installation may not expose those hardware sensors
- Use `python -m pip install -r requirements.txt` to reinstall dependencies

## License

This repository does not include a license file by default. Add one if you want to publish or share the project with explicit reuse terms.
