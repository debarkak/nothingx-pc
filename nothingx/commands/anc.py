from ..wire import Cmd, Dir, AncMode


class AncCommands:
    def __init__(self, session):
        self._s = session

    def _set(self, mode: int):
        self._s.run(Cmd.ANC_SET, Dir.SET, bytes([0x01, mode, 0x00]))

    def high(self):         self._set(AncMode.HIGH)
    def mid(self):          self._set(AncMode.MID)
    def low(self):          self._set(AncMode.LOW)
    def adaptive(self):     self._set(AncMode.ADAPTIVE)
    def off(self):          self._set(AncMode.OFF)
    def transparency(self): self._set(AncMode.TRANSPARENCY)
