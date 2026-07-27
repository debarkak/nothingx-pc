import time
from ..wire import Cmd, Dir
from ..responses import Parsers, BatteryStatus


class BatteryCommands:
    def __init__(self, session):
        self._s = session

    def get(self) -> BatteryStatus:
        pkt = self._s.run(Cmd.BATTERY, Dir.GET, b"")
        return Parsers.battery(pkt.payload)

    def watch(self, timeout=60.0):
        # listens for unsolicited battery pushes (happens on lid open/close)
        # case battery shows up in these events too
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
