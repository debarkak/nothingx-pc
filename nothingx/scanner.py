import os
import json
import socket
import logging
import subprocess
from typing import Optional

from .errors import DeviceNotFoundError, ConnectionError
from .wire import build_packet, Cmd, Dir

log = logging.getLogger(__name__)

_CACHE_DIR = os.path.expanduser("~/.cache/nothingx")


_SELECTED_FILE = os.path.join(_CACHE_DIR, "selected.json")


class Scanner:
    @staticmethod
    def _run(cmd: str) -> str:
        try:
            r = subprocess.run(["bluetoothctl", cmd], capture_output=True, text=True, timeout=2)
            return r.stdout
        except Exception as e:
            log.debug(f"bluetoothctl failed: {e}")
            return ""

    @classmethod
    def paired_devices(cls) -> list:
        out = cls._run("devices")
        devs = []
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) == 3 and parts[0] == "Device":
                devs.append({"mac": parts[1], "name": parts[2]})
        return devs

    @classmethod
    def find_all_nothing(cls) -> list:
        devs = []
        for dev in cls.paired_devices():
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
