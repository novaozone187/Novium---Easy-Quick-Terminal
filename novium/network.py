"""
network.py - WebSocket client for Novium Network

Connects to the Novium Bridge running on the server VM.
Handles temp ID assignment, verification, and error forwarding.
Supports persistent connections with automatic reconnection.
"""

import os
import sys
import json
import time
import random
import string
import socket
import threading
import traceback
from pathlib import Path
from datetime import datetime

from config import load_config, save_config, DATA_DIR
from utils import color_text, BOLD, MAGENTA, GREEN, CYAN, BLUE, YELLOW, RED, RESET, clear

try:
    from websocket import create_connection, WebSocketException, WebSocketTimeoutException
    HAS_WS = True
except ImportError:
    HAS_WS = False


DISCORD_INVITE = "https://discord.gg/nbdRSwrjZz"
RECONNECT_DELAYS = [2, 5, 15, 30, 60]
LOG_FILE = DATA_DIR / "novium_network.log"
RECV_TIMEOUT = 30


def _log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")
    except Exception:
        pass


def _generate_temp_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))


class NoviumNetwork:
    def __init__(self):
        cfg = load_config()
        saved_tid = cfg.get("network", {}).get("temp_id")
        if not saved_tid:
            saved_tid = _generate_temp_id()
            cfg.setdefault("network", {})["temp_id"] = saved_tid
            save_config(cfg)
        self.ws = None
        self.temp_id = saved_tid
        self.connected = False
        self.verified = cfg.get("network", {}).get("verified", False)
        self.client_id = cfg.get("network", {}).get("client_id")
        self._thread = None
        self._stop = False
        self._explicit_disconnect = False
        self._last_error_sent = 0
        self._pending_code = None
        self._welcome_received = False
        self._listeners = []
        self._lock = threading.Lock()

    @property
    def display_id(self):
        return self.client_id or self.temp_id

    def add_listener(self, callback):
        self._listeners.append(callback)

    def _notify(self, event, data=None):
        for cb in self._listeners:
            try:
                cb(event, data)
            except Exception:
                pass

    def _cleanup_ws(self):
        old_ws = self.ws
        self.ws = None
        if old_ws:
            try:
                if old_ws.sock:
                    old_ws.sock.settimeout(0.1)
            except Exception:
                pass
            try:
                old_ws.close()
            except Exception:
                pass

    def connect(self, url=None):
        if not HAS_WS:
            return False, "websocket-client not installed. Run: python -m pip install websocket-client"

        with self._lock:
            if self.connected:
                return False, "Already connected"
            self._cleanup_ws()

        cfg = load_config()
        url = url or cfg.get("network", {}).get("server_url", "ws://localhost:8765")

        try:
            ws = create_connection(url, timeout=10)
            ws.settimeout(RECV_TIMEOUT)

            self._explicit_disconnect = False

            with self._lock:
                self.ws = ws
                self.connected = True
                self._stop = False
                self._welcome_received = False

            hello = {
                "type": "hello",
                "temp_id": self.temp_id,
                "version": __import__("config").get_version(),
                "platform": sys.platform,
            }
            saved_cid = cfg.get("network", {}).get("client_id")
            if saved_cid:
                hello["client_id"] = saved_cid
                hello["restored"] = True
            self.ws.send(json.dumps(hello))

            with self._lock:
                self._thread = threading.Thread(target=self._listen_loop, daemon=True)
                self._thread.start()
            self._notify("connected", {"temp_id": self.temp_id})
            return True, f"Connected as {self.temp_id}"
        except Exception as e:
            with self._lock:
                self.connected = False
                self._cleanup_ws()
            err = str(e)
            if "timed out" in err.lower():
                return False, f"Connection timed out — {url} unreachable"
            if "refused" in err.lower():
                return False, f"Connection refused — is the bridge running on {url}?"
            if "certificate" in err.lower():
                return False, f"SSL certificate error — check your URL uses ws:// not wss://"
            return False, f"Connection failed: {err}"

    def disconnect(self):
        self._explicit_disconnect = True
        with self._lock:
            self._stop = True
            self.connected = False
            self._welcome_received = False
            self._cleanup_ws()

    def disconnect_with_reason(self, reason):
        if not self.connected:
            return
        try:
            self.ws.send(json.dumps({
                "type": "disconnect_request",
                "reason": reason,
                "client_id": self.client_id or self.temp_id
            }))
            time.sleep(1)
        except Exception:
            pass
        self.disconnect()

    def send_error(self, message, tb=None):
        if not self.connected:
            return
        now = time.time()
        if now - self._last_error_sent < 2:
            return
        self._last_error_sent = now
        try:
            self.ws.send(json.dumps({
                "type": "error",
                "client_id": self.client_id or self.temp_id,
                "message": str(message),
                "traceback": tb or "",
                "timestamp": datetime.utcnow().isoformat()
            }))
        except Exception:
            pass

    def send_log(self, level, message):
        if not self.connected:
            return
        try:
            self.ws.send(json.dumps({
                "type": "log",
                "client_id": self.client_id or self.temp_id,
                "level": level,
                "message": str(message),
                "timestamp": datetime.utcnow().isoformat()
            }))
        except Exception:
            pass

    def _listen_loop(self):
        last_heartbeat = time.time()
        ws = self.ws

        while not self._stop:
            try:
                raw = ws.recv()
                if raw is None:
                    _log("_listen_loop: recv returned None — connection closed")
                    break
                data = json.loads(raw)
                self._handle_message(data)
            except json.JSONDecodeError:
                continue
            except WebSocketTimeoutException:
                now = time.time()
                if now - last_heartbeat >= 30:
                    try:
                        ws.send(json.dumps({"type": "pong"}))
                        last_heartbeat = now
                    except Exception:
                        pass
                continue
            except (WebSocketException, ConnectionError, OSError) as e:
                _log(f"_listen_loop: {type(e).__name__} — {e}")
                break
            except Exception as e:
                _log(f"_listen_loop: Exception — {type(e).__name__}: {e}")
                break

        with self._lock:
            if self._stop:
                return
            self.connected = False
            self._welcome_received = False
            self._cleanup_ws()

        self._notify("disconnected", None)

        if self._explicit_disconnect:
            _log("_listen_loop: explicit disconnect — not reconnecting")
            return

        _log("_listen_loop: connection lost — starting reconnect loop")
        self._reconnect_loop()

    def _reconnect_loop(self):
        delay_idx = 0
        while not self._stop:
            delay = RECONNECT_DELAYS[min(delay_idx, len(RECONNECT_DELAYS) - 1)]
            delay_idx += 1

            _log(f"_reconnect_loop: waiting {delay}s before reconnect attempt")
            for _ in range(int(delay * 10)):
                if self._stop:
                    return
                time.sleep(0.1)

            if self._stop:
                return

            cfg = load_config()
            url = cfg.get("network", {}).get("server_url", "ws://localhost:8765")
            ok, msg = self.connect(url)
            if ok:
                _log(f"_reconnect_loop: reconnected successfully — {msg}")
                return
            _log(f"_reconnect_loop: reconnect failed — {msg}")

    def _handle_message(self, data):
        msg_type = data.get("type")
        if msg_type == "welcome":
            self._welcome_received = True
            server_client_id = data.get("assigned_id")
            server_verified = data.get("verified", False)

            if server_client_id:
                self.client_id = server_client_id
                self.verified = server_verified
                cfg = load_config()
                cfg.setdefault("network", {})
                cfg["network"]["client_id"] = server_client_id
                cfg["network"]["verified"] = server_verified
                save_config(cfg)
            elif not self.client_id:
                cfg = load_config()
                saved_cid = cfg.get("network", {}).get("client_id")
                if saved_cid:
                    self.client_id = saved_cid
                    self.verified = cfg.get("network", {}).get("verified", False)

            self._notify("welcome", data)

        elif msg_type == "verify_challenge":
            self._pending_code = data.get("code")
            code = self._pending_code or "???"
            sys.stdout.write("\n\n=============== VERIFICATION CODE ===============\n")
            sys.stdout.write(f"  Code: {code}\n")
            sys.stdout.write("===============================================\n\n")
            sys.stdout.write("Open Discord → verification channel → Confirm Code\n\n")
            sys.stdout.flush()
            self._notify("verify_challenge", data)

        elif msg_type == "verified":
            self.verified = True
            self._pending_code = None
            self.client_id = data.get("client_id", self.client_id)
            cfg = load_config()
            cfg["network"]["client_id"] = self.client_id
            cfg["network"]["verified"] = True
            save_config(cfg)
            try:
                clear()
                cid = self.client_id or "NOVIUM-???"
                print(color_text("═══════════════════════════════", BOLD + GREEN))
                print(color_text(f"  ✅ VERIFIED as {cid}!", BOLD + GREEN))
                print(color_text("═══════════════════════════════", BOLD + GREEN))
                print()
                sys.stdout.flush()
            except Exception:
                traceback.print_exc()
            self._notify("verified", data)
            try:
                time.sleep(1)
                self.ws.send(json.dumps({"type": "test_connection", "client_id": self.client_id}))
            except Exception:
                pass

        elif msg_type == "test_connection_result":
            result = data.get("success", False)
            if result:
                ch = data.get("channel", "?")
                sys.stdout.write(color_text(f"\n  ✅ Channel test passed — #{ch}\n", GREEN))
            else:
                err = data.get("error", "unknown")
                sys.stdout.write(color_text(f"\n  ⚠️ Channel test failed: {err}\n", YELLOW))
            sys.stdout.flush()
            self._notify("test_connection_result", data)

        elif msg_type == "ping":
            try:
                self.ws.send(json.dumps({"type": "pong"}))
            except Exception:
                pass

        elif msg_type == "error":
            self._notify("server_error", data)

    def status_text(self):
        if not HAS_WS:
            return "Network: websocket-client not installed"
        if not self.connected:
            return "Network: Disconnected"
        if self.verified and self.client_id:
            return f"Network: Connected ✅ (ID: {self.client_id})"
        return f"Network: Connected (unverified, temp: {self.temp_id})"


_network_instance = None


def get_network():
    global _network_instance
    if _network_instance is None:
        _network_instance = NoviumNetwork()
    return _network_instance
