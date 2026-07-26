import time
from typing import Generator
from ..wire import Cmd, Dir
from ..responses import Parsers, BatteryStatus

# Unsolicited direction byte seen on battery push packets
_UNSOLICITED_DIR = 0x00


class BatteryCommands:
    def __init__(self, session):
        self._s = session

    def get(self) -> BatteryStatus:
        pkt = self._s.run(Cmd.BATTERY, Dir.GET, b"")
        return Parsers.battery(pkt.payload)

    def watch(self, timeout: float = 60.0) -> Generator[BatteryStatus, None, None]:
        """Yield BatteryStatus whenever the device pushes a battery update.

        Battery push events happen on lid open/close and contain case battery
        (tag 0x04) in addition to left (0x02) and right (0x03) earbud levels.
        Keeps the connection alive for *timeout* seconds listening for events.
        """
        deadline = time.time() + timeout
        self._s._conn.sock.settimeout(0.3)
        while time.time() < deadline:
            try:
                data = self._s._conn.recv(4096)
                if data:
                    self._s._parser.feed(data)
            except OSError:
                pass
            while True:
                pkt = self._s._parser.next()
                if pkt is None:
                    break
                if pkt.cmd == Cmd.BATTERY and pkt.payload:
                    yield Parsers.battery(pkt.payload)

    def __call__(self) -> BatteryStatus:
        return self.get()
