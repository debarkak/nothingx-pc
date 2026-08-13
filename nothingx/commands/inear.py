from ..wire import Cmd, Dir


class InEarCommands:
    def __init__(self, session):
        self._s = session

    def get(self) -> bool:
        pkt = self._s.run(Cmd.IN_EAR, Dir.GET, b"")
        if not pkt or len(pkt.payload) < 3:
            return False
        p = pkt.payload
        # Standard format: [0x02, 0x01, state, 0x02, ...] or [0x01, state, ...]
        if len(p) >= 3 and p[0] == 0x02 and p[1] == 0x01:
            return p[2] == 0x01
        elif len(p) >= 2 and p[0] == 0x01:
            return p[1] == 0x01
        return False

    def set(self, enable: bool):
        import time
        val = 0x01 if enable else 0x00
        payload = bytes([0x02, 0x01, val])
        try:
            self._s.send(Cmd.IN_EAR, Dir.SET, payload)
        except Exception:
            pass
        time.sleep(0.15)

    def on(self):
        self.set(True)

    def off(self):
        self.set(False)
