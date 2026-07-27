from typing import Optional
from .scanner import Scanner, RFCOMMConnection
from .session import Session
from .commands import AncCommands, BatteryCommands, FindCommands, FitCommands, InfoCommands
from .errors import DeviceNotFoundError


class Device:
    def __init__(self, mac: str, name: str = "Nothing Earbuds"):
        self.mac = mac
        self.name = name
        self._conn = RFCOMMConnection(mac)
        self._session = Session(self._conn)

        self.anc     = AncCommands(self._session)
        self.battery = BatteryCommands(self._session)
        self.find    = FindCommands(self._session)
        self.fit     = FitCommands(self._session)
        self.info    = InfoCommands(self._session)

    def connect(self):
        self._conn.connect()

    def disconnect(self):
        self._conn.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    @classmethod
    def discover(cls) -> "Device":
        found = Scanner.find_nothing()
        if not found:
            raise DeviceNotFoundError("no Nothing device found in paired devices")
        d = cls(found["mac"], found["name"])
        d.connect()
        return d

    @classmethod
    def from_name(cls, name: str) -> "Device":
        found = Scanner.find_by_name(name)
        if not found:
            raise DeviceNotFoundError(f"no paired device matching '{name}'")
        d = cls(found["mac"], found["name"])
        d.connect()
        return d

    @classmethod
    def from_mac(cls, mac: str) -> "Device":
        d = cls(mac)
        d.connect()
        return d
