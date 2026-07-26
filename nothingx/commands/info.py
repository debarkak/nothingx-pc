from ..wire import Cmd, Dir
from ..responses import Parsers


class InfoCommands:
    def __init__(self, session):
        self._s = session

    def firmware(self) -> str:
        pkt = self._s.run(Cmd.FIRMWARE, Dir.GET, b"")
        return Parsers.firmware(pkt.payload)
