from ..wire import Cmd, Dir
from ..responses import Parsers, BatteryStatus


class BatteryCommands:
    def __init__(self, session):
        self._s = session

    def get(self) -> BatteryStatus:
        pkt = self._s.run(Cmd.BATTERY, Dir.GET, b"")
        return Parsers.battery(pkt.payload)

    def __call__(self) -> BatteryStatus:
        return self.get()
