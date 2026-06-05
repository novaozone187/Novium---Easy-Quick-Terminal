import subprocess
import socket
import re
import ipaddress
import platform as plat
import os as _os
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import color_text, BOLD, GREEN, CYAN, YELLOW, MAGENTA, RED, RESET

PROBE_PORTS = [80, 443, 22, 8080, 8443]

MAC_VENDORS = {
    "00:00:0C": "Cisco", "00:01:5C": "Alcatel-Lucent", "00:03:93": "Apple",
    "00:05:69": "Apple", "00:0A:27": "Apple", "00:0A:95": "Apple",
    "00:0D:93": "Apple", "00:10:FA": "Apple", "00:11:24": "Apple",
    "00:14:51": "Apple", "00:17:F2": "Apple", "00:1B:63": "Apple",
    "00:1E:52": "Apple", "00:1F:5B": "Apple", "00:1F:F3": "Apple",
    "00:21:E9": "Apple", "00:22:41": "Apple", "00:23:32": "Apple",
    "00:23:6C": "Apple", "00:23:DF": "Apple", "00:24:36": "Apple",
    "00:25:00": "Apple", "00:25:BC": "Apple", "00:26:08": "Apple",
    "00:26:4A": "Apple", "00:26:B0": "Apple", "00:50:56": "VMware",
    "00:0C:29": "VMware", "00:05:69": "VMware", "00:50:EB": "Microsoft",
    "00:03:FF": "Microsoft", "00:0D:3A": "Intel", "00:1B:21": "Intel",
    "00:1E:67": "Intel", "00:21:6B": "Intel", "00:24:D7": "Intel",
    "38:F3:AB": "Samsung", "00:1E:DF": "Samsung", "00:23:D4": "Samsung",
    "3C:07:54": "Huawei", "00:25:9E": "Huawei", "00:1A:2B": "Huawei",
    "00:0F:E2": "D-Link", "1C:7E:E5": "D-Link", "00:1B:11": "TP-Link",
    "14:CF:20": "TP-Link", "A0:F3:C1": "TP-Link", "F4:EC:38": "TP-Link",
    "00:15:6D": "ASUS", "00:1A:92": "ASUS", "10:BF:48": "ASUS",
    "BC:EE:7B": "ASUS", "C0:EE:FB": "ASUS", "B8:27:EB": "Raspberry Pi",
    "DC:A6:32": "Raspberry Pi", "E4:5F:01": "Raspberry Pi",
    "00:23:AE": "Synology", "00:11:32": "Synology", "00:24:1D": "Roku",
    "00:0A:5E": "Sonos", "00:17:88": "Nest", "18:B4:30": "Amazon",
    "00:23:AA": "Amazon", "AC:63:BE": "Google", "8C:DE:F9": "Google",
    "A4:77:33": "Google", "18:8B:9D": "Google", "3C:5A:B4": "Google",
    "10:AE:60": "Google", "00:1A:11": "Google", "F8:8C:21": "Google",
    "00:04:4B": "Bosch", "00:0F:55": "Philips", "EC:1A:59": "Philips",
    "00:12:4B": "Honeywell", "00:16:17": "Panasonic", "00:17:31": "Panasonic",
    "00:1A:2B": "Xiaomi", "00:9A:CD": "Xiaomi", "18:FE:34": "Xiaomi",
    "00:23:7D": "ZTE", "00:25:9E": "Canon", "00:1E:58": "Canon",
    "00:17:08": "Epson", "00:1B:EE": "HP", "00:21:5A": "HP",
    "3C:D9:2B": "HP", "00:1D:D4": "Belkin", "00:22:75": "Belkin",
    "00:1A:6B": "Netgear", "20:E5:2A": "Netgear", "A0:21:B7": "Netgear",
    "00:1B:2F": "Lenovo", "00:24:BE": "Lenovo", "3C:7C:3F": "Dell",
    "00:14:22": "Dell", "00:1E:4F": "Dell", "00:21:9B": "Dell",
    "00:1A:A0": "Acer", "00:1D:72": "Acer", "C8:5B:76": "Acer",
    "00:1C:C0": "LG", "00:1E:66": "LG", "00:22:44": "LG",
    "00:25:07": "Toshiba", "00:15:B9": "Toshiba", "00:24:4B": "Xerox",
    "00:21:7C": "Ubiquiti", "24:A4:3C": "Ubiquiti", "04:18:D6": "Ubiquiti",
    "80:2A:A8": "Ubiquiti", "00:27:22": "MikroTik", "4C:5E:0C": "MikroTik",
    "00:1B:4E": "Supermicro", "00:25:90": "Supermicro", "00:90:27": "Supermicro",
    "4C:BA:D7": "LG Electronics", "00:CB:7A": "Arris", "2C:FE:E2": "Sercomm",
    "BC:24:11": "Raspberry Pi", "54:04:A6": "Arris", "10:17:A0": "Arris",
    "04:BF:6D": "Vodafone", "84:8C:8D": "AVM", "98:DE:D0": "AVM",
    "2C:3E:CF": "AVM", "4C:ED:DE": "AVM", "CC:2D:8C": "AVM",
    "00:23:5A": "Sony", "00:24:47": "Sony", "C0:16:8A": "Wyze",
    "00:22:6B": "Ring", "74:75:48": "Ring", "00:0C:43": "TP-Link",
    "EC:06:6B": "Uniden", "8C:AE:4C": "Foscam", "00:1A:6C": "Planet",
    "00:09:6B": "Extreme Networks", "00:0F:3D": "Enterasys",
    "00:E0:4C": "Realtek", "00:1B:A9": "Atheros", "00:1F:29": "Broadcom",
    "00:1D:7D": "Cisco-Linksys", "00:18:39": "Cisco-Linksys",
    "00:12:17": "Cisco-Linksys", "00:14:BF": "Cisco-Linksys",
    "00:DA:55": "Apple", "F0:18:98": "Cisco", "70:3A:CB": "Cisco",
    "00:1D:A1": "Cisco", "00:1E:79": "Aruba", "00:0F:B5": "Aruba",
    "00:1C:0E": "Juniper", "00:1A:30": "Juniper", "00:1F:6C": "Fortinet",
    "00:09:0F": "Sophos", "00:1B:17": "Sophos", "00:1E:4C": "Palo Alto",
    "00:1C:58": "Check Point", "00:1B:D4": "Barracuda",
}

PORT_LABELS = {
    80: "HTTP", 443: "HTTPS", 22: "SSH", 8080: "HTTP-alt", 8443: "HTTPS-alt",
    445: "SMB", 135: "RPC", 3389: "RDP", 5900: "VNC", 21: "FTP", 23: "Telnet",
    25: "SMTP", 53: "DNS", 110: "POP3", 143: "IMAP", 993: "IMAPS", 995: "POP3S",
    139: "NetBIOS", 389: "LDAP", 636: "LDAPS", 3306: "MySQL", 5432: "PostgreSQL",
    27017: "MongoDB", 6379: "Redis", 11211: "Memcached", 161: "SNMP",
    9100: "Printer", 515: "LPD", 631: "IPP", 548: "AFP",
}


def get_local_subnet():
    import psutil
    addrs = psutil.net_if_addrs()
    for _, addr_list in addrs.items():
        for addr in addr_list:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                try:
                    ip = ipaddress.IPv4Address(addr.address)
                    netmask = ipaddress.IPv4Address(addr.netmask)
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    return str(network), str(ip)
                except (ValueError, AttributeError):
                    continue
    return None, None


def _probe_host(ip):
    """Stealth probe: try TCP connect to common ports (looks like normal traffic)."""
    open_ports = []
    for port in PROBE_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.7)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append(port)
            s.close()
        except Exception:
            pass
    return open_ports


def probe_sweep(network):
    net = ipaddress.IPv4Network(network, strict=False)
    hosts = list(net.hosts())
    if len(hosts) > 254:
        hosts = hosts[:254]
    results = {}
    with ThreadPoolExecutor(max_workers=50) as pool:
        fut_map = {pool.submit(_probe_host, str(h)): str(h) for h in hosts}
        for fut in as_completed(fut_map):
            ip = fut_map[fut]
            try:
                ports = fut.result()
                if ports:
                    results[ip] = ports
            except Exception:
                pass
    return results


def parse_arp():
    system = plat.system().lower()
    devices = []
    try:
        if system == "windows":
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                m = re.match(r'^\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})', line)
                if m:
                    mac = m.group(2).replace("-", ":").upper()
                    devices.append({"ip": m.group(1), "mac": mac})
        else:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                m = re.match(r'.*\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]{17})', line)
                if m:
                    mac = m.group(2).upper()
                    devices.append({"ip": m.group(1), "mac": mac})
    except Exception:
        pass
    return devices


def resolve_name(ip, timeout=3):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except Exception:
        return None


def resolve_netbios(ip):
    """NetBIOS name resolution (Windows only)."""
    if _os.name != "nt":
        return None
    try:
        result = subprocess.run(["nbtstat", "-A", ip], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            if "<00>" in line and "UNIQUE" in line.upper():
                parts = line.split()
                if parts:
                    return parts[0].strip()
    except Exception:
        pass
    return None


def lookup_vendor(mac):
    prefix = mac[:8]
    return MAC_VENDORS.get(prefix)


def guess_type(mac, hostname, vendor, ports=None):
    ports = ports or []

    if hostname:
        hl = hostname.lower()
        if any(x in hl for x in ("iphone", "ipad", "macbook", "imac", "apple")):
            return "Apple Device"
        if any(x in hl for x in ("samsung", "galaxy")):
            return "Mobile/Tablet"
        if "laptop" in hl or "notebook" in hl:
            return "Laptop"
        if any(x in hl for x in ("desktop", "pc", "deskto")):
            return "Desktop"
        if any(x in hl for x in ("printer", "print", "brother", "epson")):
            return "Printer"
        if any(x in hl for x in ("server", "nas", "synology", "qnap", "storage")):
            return "Server/NAS"
        if any(x in hl for x in ("router", "gateway", "ap", "access-point", "wifi", "mesh")):
            return "Router/AP"
        if any(x in hl for x in ("tv", "television", "samsung", "lg")):
            return "TV"
        if any(x in hl for x in ("camera", "cam", "dvr", "nvr")):
            return "Camera"
        if any(x in hl for x in ("speaker", "sonos", "echo", "alexa", "homepod")):
            return "Speaker"
        if any(x in hl for x in ("light", "bulb", "hue", "switch", "plug")):
            return "Smart Device"
        if any(x in hl for x in ("thermostat", "nest")):
            return "Smart Home"
        if any(x in hl for x in ("vmware", "virtual", "vm-", "kvm", "hyper-v")):
            return "Virtual Machine"
        if any(x in hl for x in ("raspberry", "rpi", "pi-", "odroid", "jetson")):
            return "Single-Board Computer"
        if any(x in hl for x in ("phone", "mobile", "android", "xiaomi")):
            return "Phone"

    if vendor:
        known = {
            "Apple": "Apple Device", "Samsung": "Mobile/Tablet",
            "Raspberry Pi": "Single-Board Computer", "TP-Link": "Router/AP",
            "Cisco": "Network Device", "Google": "Google Device",
            "Amazon": "Smart Speaker", "VMware": "Virtual Machine",
            "D-Link": "Router/AP", "ASUS": "Router/AP",
            "Sonos": "Speaker", "Nest": "Smart Home",
            "Synology": "Server/NAS", "Ubiquiti": "Network Device",
            "MikroTik": "Network Device", "Philips": "Smart Light",
            "Belkin": "Router/AP", "Netgear": "Router/AP",
            "Xiaomi": "IoT Device", "Bosch": "IoT Device",
            "Roku": "Streaming Device", "HP": "Printer",
            "Canon": "Printer", "Epson": "Printer", "Xerox": "Printer",
            "Arris": "Cable Modem/Router", "Sercomm": "ISP Device",
            "AVM": "Fritz!Box Router", "Wyze": "Camera",
            "Ring": "Security Camera", "Sony": "PlayStation/TV",
            "LG Electronics": "TV",
        }
        return known.get(vendor, vendor)

    if 22 in ports:
        return "Server/Linux"
    if 445 in ports or 139 in ports:
        return "Windows Device"
    if 80 in ports or 443 in ports or 8080 in ports:
        return "Web Device"

    return "Unknown"


def scan(deep=False):
    network_str, own_ip = get_local_subnet()
    if not network_str:
        return None, "Could not detect local network"

    net = ipaddress.IPv4Network(network_str, strict=False)

    port_results = {}
    if deep:
        port_results = probe_sweep(network_str)

    raw = parse_arp()

    devices = []
    for d in raw:
        try:
            ip = ipaddress.IPv4Address(d["ip"])
            if ip not in net:
                continue
            if own_ip and str(ip) == own_ip:
                continue
            if d["mac"].startswith("FF:FF:FF") or d["mac"].startswith("00:00:00"):
                continue
            hostname = resolve_name(d["ip"])
            if not hostname:
                hostname = resolve_netbios(d["ip"])
            vendor = lookup_vendor(d["mac"])
            open_ports = port_results.get(d["ip"], [])
            d["hostname"] = hostname or "N/A"
            d["vendor"] = vendor or "Unknown"
            d["type"] = guess_type(d["mac"], hostname, vendor, open_ports)
            d["ports"] = open_ports
            devices.append(d)
        except (ValueError, IndexError):
            continue

    seen = set()
    unique = []
    for d in devices:
        key = (d["ip"], d["mac"])
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique, None
