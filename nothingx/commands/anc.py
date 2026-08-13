from ..wire import Cmd, Dir, AncMode


class AncCommands:
    def __init__(self, session):
        self._s = session

    def _set(self, mode: int):
        self._s.run(Cmd.ANC_SET, Dir.SET, bytes([0x01, mode, 0x00]))

    def get(self) -> str:
        pkt = self._s.run(Cmd.ANC_GET, Dir.GET, b"")
        if not pkt or len(pkt.payload) < 2:
            return "unknown"
        p = pkt.payload
        if p[0] == 0x01:
            m = p[1]
        elif len(p) >= 5 and p[3] == 0x01:
            m = p[4]
        else:
            m = p[1]

        for name, value in AncMode.__members__.items():
            if value == m:
                return name.lower()
        return "unknown"

    def high(self):         self._set(AncMode.HIGH)
    def mid(self):          self._set(AncMode.MID)
    def low(self):          self._set(AncMode.LOW)
    def adaptive(self):     self._set(AncMode.ADAPTIVE)
    def off(self):          self._set(AncMode.OFF)
    def transparency(self): self._set(AncMode.TRANSPARENCY)
