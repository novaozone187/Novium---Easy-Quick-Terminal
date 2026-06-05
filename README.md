# Novium

Novium is a terminal-based system dashboard, app launcher, and performance toolkit for **Windows, macOS, and Linux**. It combines live system monitoring, LAN scanning, Novium Network client, performance & security checks, and a customizable shell — all with zero manual setup.

## Features

- **Zero-config install** — auto-installs all Python dependencies on first launch
- **Live system stats** — real-time CPU, memory, disk, temperature, fan RPM (press Q to stop)
- **LAN scanner** — passive ARP scan with deep TCP probe mode (`scanLAN [-d]`)
- **Novium Network** — WebSocket client for remote management (connect, status, disconnect, invite)
- **Performance check** — scans power plan, GPU driver, disk health, memory, startup items, pending reboot; auto-fixes issues on confirmation (`perfcheck`)
- **Security check** — scans Windows Defender, firewall, UAC, suspicious processes, network connections, startup entries (`seccheck`)
- **Auto-installs fastfetch** — OS logo/system info display (Linux, macOS, Windows)
- **Auto-update from GitHub** — checks for updates on launch, downloads zipball, applies with config backup, auto-restarts
- **Cross-platform** — same experience on Windows, macOS, Linux
- **Logo switcher** — Novium ASCII, OS logo (fastfetch), or none
- **Color customization** — 6 logo/border colors
- **Desktop shortcut + autostart** — first-run wizard or settings menu
- **Font manager** — set terminal font (monocraft, default)
- **App install shortcuts** — `install steam`, `discord`, `vscode`, `chrome`, `firefox`, `node`, `git`

## Quick Install

**Copy and paste the ENTIRE block for your OS below.** Each block installs Python (if missing), clones the repo, installs dependencies, and runs Novium.

### Windows (PowerShell)

> If Python is not installed: download from https://www.python.org/downloads/ (check **"Add Python to PATH"**) and restart your terminal first.

```powershell
python --version
git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git
cd Novium---Easy-Quick-Terminal\novium
python -m pip install -r requirements.txt
python novium.py
```

### Ubuntu / Debian

```bash
sudo apt update && sudo apt install python3 python3-pip git -y && git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git && cd Novium---Easy-Quick-Terminal/novium && python3 -m pip install -r requirements.txt && python3 novium.py
```

### Fedora

```bash
sudo dnf install python3 python3-pip git -y && git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git && cd Novium---Easy-Quick-Terminal/novium && python3 -m pip install -r requirements.txt && python3 novium.py
```

### Arch Linux

```bash
sudo pacman -S python python-pip git --noconfirm && git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git && cd Novium---Easy-Quick-Terminal/novium && python -m pip install -r requirements.txt && python novium.py
```

### openSUSE

```bash
sudo zypper install python3 python3-pip git -y && git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git && cd Novium---Easy-Quick-Terminal/novium && python3 -m pip install -r requirements.txt && python3 novium.py
```

### Alpine

```bash
sudo apk add python3 py3-pip git && git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git && cd Novium---Easy-Quick-Terminal/novium && python3 -m pip install -r requirements.txt && python3 novium.py
```

### macOS (Homebrew)

```bash
brew install python3 git && git clone https://github.com/novaozone187/Novium---Easy-Quick-Terminal.git && cd Novium---Easy-Quick-Terminal/novium && python3 -m pip install -r requirements.txt && python3 novium.py
```

### Verify Python (any OS)

Use these to check your version before installing:

| OS | Command |
|----|---------|
| Windows | `python --version` |
| Linux/macOS | `python3 --version` |

### Fallback (deps only)

If auto-install on first launch fails, run this from the `novium/` directory:

```bash
# Windows
python -m pip install -r requirements.txt

# Linux / macOS
python3 -m pip install -r requirements.txt
```

Then run `python(3) novium.py`.

## First-Run Setup

On first launch, Novium:
1. Shows an animated splash screen
2. Detects environment (Python, OS, browser, psutil, fastfetch)
3. Runs a setup wizard: desktop shortcut, autostart, logo color, feature toggles
4. Auto-connects to the Novium Network if configured
5. Saves preferences to `config.json`

## Commands

### Core

| Command | Description |
|---------|-------------|
| `help` | Show all commands (categorized with tables) |
| `stats` | Live system stats (refreshes every 2s, Q to stop) |
| `fan` | Temperature and fan sensor screen |
| `sysinfo` | Detailed system information |
| `nhome` | Return to the Novium home screen |
| `clear` | Clear the screen |
| `exit` | Quit Novium |

### Utilities

| Command | Description |
|---------|-------------|
| `scanLAN [-d]` | Passive ARP LAN scan; `-d` deep probes ports 80,443,22,8080,8443 |
| `web <query>` | Open Google search in browser |
| `app <name>` | Launch or search for an application |
| `install <app>` | Install apps: steam, discord, vscode, chrome, firefox, node, git |

### Security

| Command | Description |
|---------|-------------|
| `perfcheck` | Scan 8 performance areas; auto-fixes issues on confirmation |
| `seccheck` | Scan for security issues (Defender, firewall, UAC, suspicious processes, network, startup) |

### System

| Command | Description |
|---------|-------------|
| `update` | Check for updates → downloads + applies + restarts |
| `os-setup` | OS setup wizard (driver & app recommendations) |
| `winactivate` | Run Windows activation script (Windows only) |
| `ff` | Run fastfetch (auto-installs if missing) |
| `logo` | Switch logo: Novium / OS (fastfetch) / None |
| `color <C>` | Change logo/border color: BLUE, CYAN, MAGENTA, GREEN, YELLOW, RED |

### Version & Font

| Command | Description |
|---------|-------------|
| `version` | Show current Novium version |
| `font set <name>` | Set terminal font (monocraft, default) |
| `font list` | List available fonts |
| `font current` | Show current font |

### Novium Network

| Command | Description |
|---------|-------------|
| `novium connect [url]` | Connect to Novium Network (default: ws://localhost:8765) |
| `novium status` | Show connection and verification status |
| `novium disconnect` | Disconnect from network (logs reason) |
| `novium invite` | Open Discord invite to the Novium server |
| `network` | Alias for `novium` prefix |

### Setup

| Command | Description |
|---------|-------------|
| `settings` | Open settings menu (shortcuts, autostart, features, network) |
| `setup` | Rerun first-run setup wizard |
| `nuke` | Completely remove Novium from your system |
| `nrestart` | Restart Novium (applies file updates) |

Any other input is executed as a system command (`dir` on Windows, `ls` on Linux, etc.).

## Auto-Update

Novium checks [GitHub releases](https://github.com/novaozone187/Novium---Easy-Quick-Terminal/releases) on launch:

- Backs up current files to `.novium_backup/`
- Downloads the latest release zipball
- Extracts and overwrites all files (preserving `config.json`, `.version`, logs)
- Updates the version file
- Auto-restarts via `nrestart`

Manual trigger: `update` (prompts for confirmation).

## Performance Check (`perfcheck`)

Scans 8 areas and auto-fixes when possible:

| Check | Auto-Fix |
|-------|----------|
| Power Plan | Switches to High Performance |
| GPU Driver | Opens dxdiag for manual check |
| Pending Reboot | Initiates restart |
| Disk Health | Alerts on failing drives |
| Memory Usage | Recommends closing apps |
| Disk Space | Runs Disk Cleanup (cleanmgr) |
| Startup Programs | Flags excessive items |
| CPU | Reports cores/frequency |

## Security Check (`seccheck`)

Scans 6 security areas:

| Check | What It Looks For |
|-------|-------------------|
| Windows Defender | Service running or stopped |
| Firewall | Enabled on all 3 profiles |
| UAC | Enabled or disabled |
| Suspicious Processes | Scripts running from temp dirs, abnormal CPU |
| Network Connections | Established count, high-port listeners |
| Startup Entries | Number of auto-start items |

## LAN Scanner (`scanLAN`)

Passive scan reads the ARP table — no packets sent, completely stealth.

**Deep mode** (`-d`): TCP connects to ports 80, 443, 22, 8080, 8443 on each discovered host to identify services and guess device type (e.g., port 22 → "Server/Linux", port 445 → "Windows Device").

Also resolves NetBIOS names on Windows and looks up MAC vendor by OUI (~300 vendors).

## Configuration

File: `config.json` (auto-created on first run).

```json
{
  "font": "default",
  "logo_color": "BLUE",
  "logo_mode": "novium",
  "hardware_monitoring": true,
  "web_search_enabled": true,
  "app_launcher_active": false,
  "autostart_enabled": false,
  "network": {
    "enabled": false,
    "server_url": "ws://localhost:8765",
    "client_id": null,
    "verified": false
  }
}
```

Edit directly or use `settings` → Manage Features.

## OS-Specific Tips

### Windows
- Use `python` (not `python3`)
- Run `winactivate` for Windows activation
- `font set monocraft` for a dev-friendly terminal font
- Deep LAN scan includes NetBIOS name resolution
- Performance fix: `cleanmgr` opens Disk Cleanup GUI

### Linux
- Use `python3` (or `python` if on Arch)
- Install `smartmontools` for disk health checks (`sudo apt install smartmontools`)
- Install `pciutils` for GPU detection (`sudo apt install pciutils`)
- Fastfetch installs via `apt`, `dnf`, `pacman`, `zypper`, or `apk`
- `seccheck` skips Windows-specific checks (Defender, firewall, UAC)
- `perfcheck` recommends checking cpufreq governor manually
- Kernel updates requiring reboot: checked via `/var/run/reboot-required`

### macOS
- Use `python3`
- Install via Homebrew: `brew install python3 fastfetch`
- Temperature/fan sensors limited on some Mac hardware

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Dependencies won't install | Ensure Python 3.10+ and pip are available; run `pip install -r requirements.txt` manually |
| No sensor data | Platform/hardware doesn't expose sensors — normal on some systems |
| fastfetch not found | Run `ff` to auto-install, or install via your package manager |
| Colors not showing | Windows: enable ANSI via `set_windows_ansi()` (done automatically). Old terminals may not support ANSI |
| Desktop shortcut closes | Ensure shortcut target is `python(3) novium.py` in the novium directory |
| Update fails | Check `.novium_backup/` for your previous files; restore manually |

## Uninstall

1. `nuke` inside Novium — removes shortcuts, autostart, config, and `psutil`
2. Delete the novium folder manually

## Requirements

- Python 3.10+
- No manual dependency install needed — auto-installed: `psutil`, `websocket-client`

## License

This repository does not include a license file by default. Add one if you want to publish or share the project with explicit reuse terms.
