import os
import sys
import json
import socket
import logging
import subprocess
from typing import Optional

from .errors import DeviceNotFoundError, ConnectionError
from .wire import build_packet, Cmd, Dir

log = logging.getLogger(__name__)

if sys.platform == "win32":
    _CACHE_DIR = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "nothingx")
else:
    _CACHE_DIR = os.path.expanduser("~/.cache/nothingx")

_SELECTED_FILE = os.path.join(_CACHE_DIR, "selected.json")


class Scanner:
    @staticmethod
    def _run(*args) -> str:
        try:
            r = subprocess.run(["bluetoothctl", *args], capture_output=True, text=True, timeout=2)
            return r.stdout
        except Exception as e:
            log.debug(f"bluetoothctl failed: {e}")
            return ""

    @classmethod
    def _paired_devices_windows(cls) -> list:
        devs = []
        try:
            import winreg
            key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as k:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                        mac = ":".join(sub[j:j+2] for j in range(0, 12, 2)).upper()
                        name = None
                        with winreg.OpenKey(k, sub) as sub_k:
                            for val_name in ("Name", "FriendlyName"):
                                try:
                                    raw, _ = winreg.QueryValueEx(sub_k, val_name)
                                    if isinstance(raw, bytes):
                                        decoded = raw.decode("utf-8", errors="ignore").rstrip("\x00")
                                    else:
                                        decoded = str(raw).rstrip("\x00")
                                    if decoded.strip():
                                        name = decoded.strip()
                                        break
                                except OSError:
                                    pass
                        if name:
                            devs.append({"mac": mac, "name": name})
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            log.debug(f"winreg device query failed: {e}")

        if not devs:
            try:
                ps = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-PnpDevice -Class Bluetooth | Where-Object { $_.InstanceId -like '*DEV_*' } | Select-Object FriendlyName, InstanceId | ConvertTo-Json -Compress"],
                    capture_output=True, text=True, timeout=3
                )
                if ps.stdout.strip():
                    data = json.loads(ps.stdout)
                    if isinstance(data, dict):
                        data = [data]
                    for item in data:
                        inst = item.get("InstanceId", "")
                        fname = item.get("FriendlyName", "")
                        if "DEV_" in inst and fname:
                            raw_mac = inst.split("DEV_")[1].split("\\")[0].split("&")[0]
                            if len(raw_mac) == 12:
                                mac = ":".join(raw_mac[j:j+2] for j in range(0, 12, 2)).upper()
                                devs.append({"mac": mac, "name": fname})
            except Exception as e:
                log.debug(f"powershell fallback failed: {e}")

        return devs

    @classmethod
    def _connected_audio_endpoints_windows(cls) -> set:
        try:
            ps = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-PnpDevice -Class AudioEndpoint -Status OK | Select-Object -ExpandProperty FriendlyName"],
                capture_output=True, text=True, timeout=2
            )
            return {line.strip().lower() for line in ps.stdout.splitlines() if line.strip()}
        except Exception:
            return set()

    @classmethod
    def paired_devices(cls) -> list:
        if sys.platform == "win32":
            return cls._paired_devices_windows()
        out = cls._run("devices")
        devs = []
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) == 3 and parts[0] == "Device":
                devs.append({"mac": parts[1], "name": parts[2]})
        return devs

    @classmethod
    def connected_devices(cls) -> list:
        if sys.platform == "win32":
            paired = cls.paired_devices()
            active_endpoints = cls._connected_audio_endpoints_windows()
            connected = []
            for d in paired:
                d_name = d["name"].lower()
                if any(d_name in ep for ep in active_endpoints):
                    connected.append(d)
            return connected
        out = cls._run("devices", "Connected")
        devs = []
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) == 3 and parts[0] == "Device":
                devs.append({"mac": parts[1], "name": parts[2]})
        return devs

    @classmethod
    def is_connected(cls, mac: str) -> bool:
        if sys.platform == "win32":
            conn = cls.connected_devices()
            return any(d["mac"].upper() == mac.upper() for d in conn)
        out = cls._run("info", mac)
        return "Connected: yes" in out

    @classmethod
    def find_all_nothing(cls) -> list:
        devs = []
        for dev in cls.paired_devices():
            n = dev["name"].lower()
            if "nothing" in n or "ear" in n or "cmf" in n:
                devs.append(dev)
        return devs

    @classmethod
    def find_connected_nothing(cls) -> list:
        devs = []
        for dev in cls.connected_devices():
            n = dev["name"].lower()
            if "nothing" in n or "ear" in n or "cmf" in n:
                devs.append(dev)
        return devs

    @classmethod
    def get_selected(cls) -> Optional[dict]:
        if os.path.exists(_SELECTED_FILE):
            try:
                with open(_SELECTED_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    @classmethod
    def set_selected(cls, dev: dict):
        os.makedirs(_CACHE_DIR, exist_ok=True)
        try:
            with open(_SELECTED_FILE, "w") as f:
                json.dump(dev, f)
        except Exception:
            pass

    @classmethod
    def find_nothing(cls) -> Optional[dict]:
        all_devs = cls.find_all_nothing()
        if not all_devs:
            return None

        # Automatically check which Nothing audio device is actually connected via Bluetooth
        connected_nothing = cls.find_connected_nothing()
        if len(connected_nothing) == 1:
            cls.set_selected(connected_nothing[0])
            return connected_nothing[0]
        elif len(connected_nothing) > 1:
            selected = cls.get_selected()
            if selected:
                for dev in connected_nothing:
                    if dev["mac"] == selected["mac"]:
                        return dev
            cls.set_selected(connected_nothing[0])
            return connected_nothing[0]

        # Fallback if no device is currently reporting Connected state
        selected = cls.get_selected()
        if selected:
            for dev in all_devs:
                if dev["mac"] == selected["mac"]:
                    return dev

        return all_devs[0]

    @classmethod
    def find_by_name(cls, query: str) -> Optional[dict]:
        for dev in cls.paired_devices():
            if query.lower() in dev["name"].lower() or query.lower() == dev["mac"].lower():
                return dev
        return None


class RFCOMMConnection:
    def __init__(self, mac: str):
        self.mac = mac
        self.port: Optional[int] = None
        self.sock: Optional[socket.socket] = None

        os.makedirs(_CACHE_DIR, exist_ok=True)
        self._cache = os.path.join(_CACHE_DIR, mac.replace(":", "_") + ".json")

    def _load_cached_port(self) -> Optional[int]:
        if os.path.exists(self._cache):
            try:
                with open(self._cache) as f:
                    return json.load(f).get("port")
            except Exception:
                pass
        return None

    def _save_port(self, port: int):
        try:
            with open(self._cache, "w") as f:
                json.dump({"port": port}, f)
        except Exception:
            pass

    def connect(self):
        if self.sock:
            return

        cached = self._load_cached_port()
        ports = [cached] if cached else []
        ports += [p for p in range(1, 31) if p != cached]

        probe = build_packet(Cmd.DEVICE_INFO, Dir.GET, [])

        for p in ports:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.settimeout(1.5)
            try:
                s.connect((self.mac, p))
                s.send(probe)
                resp = s.recv(1024)
                if not resp or not (resp.startswith(b"\x55\x60") or resp.startswith(b"\x55\x00")):
                    s.close()
                    continue
                self.sock = s
                self.port = p
                self._save_port(p)
                s.settimeout(5.0)
                log.info(f"connected to {self.mac} on RFCOMM {p}")
                return
            except OSError:
                s.close()

        raise ConnectionError(f"couldn't connect to {self.mac} on any RFCOMM port")

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, data: bytes):
        if not self.sock:
            raise ConnectionError("not connected")
        try:
            log.debug(f"TX: {data.hex()}")
            self.sock.send(data)
        except OSError as e:
            self.disconnect()
            raise ConnectionError(f"send failed: {e}")

    def recv(self, size: int = 1024) -> bytes:
        if not self.sock:
            raise ConnectionError("not connected")
        try:
            data = self.sock.recv(size)
            if data:
                log.debug(f"RX: {data.hex()}")
            return data
        except socket.timeout:
            return b""
        except OSError as e:
            self.disconnect()
            raise ConnectionError(f"recv failed: {e}")
