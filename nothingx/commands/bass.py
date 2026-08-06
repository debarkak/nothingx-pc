from ..wire import Cmd, Dir


class BassCommands:
    def __init__(self, session):
        self._s = session

    def get(self) -> dict:
        pkt = None
        try:
            pkt = self._s.run(Cmd.ENHANCED_BASS, Dir.GET, b"")
        except Exception:
            pass
        if not pkt or len(pkt.payload) < 2:
            return {"enabled": False, "level": 0}
        enabled = bool(pkt.payload[0])
        raw_level = pkt.payload[1]
        if not enabled or raw_level == 0:
            return {"enabled": False, "level": 0, "raw_level": 0}
        level = max(1, min(5, round(raw_level / 2)))
        return {"enabled": True, "level": level, "raw_level": raw_level}

    def set(self, enable: bool, level: int = 5):
        import time
        if not enable or level == 0:
            payload = bytes([0, 0])
        else:
            clamped_level = max(1, min(5, level))
            raw_level = clamped_level * 2
            payload = bytes([1, raw_level])

        try:
            self._s.send(0x51, Dir.SET, payload)
        except Exception:
            pass
        time.sleep(0.15)
        try:
            self._s.send(Cmd.ENHANCED_BASS, Dir.SET, payload)
        except Exception:
            pass
        time.sleep(0.15)

    def on(self, level: int = 5):
        self.set(True, level)

    def off(self):
        self.set(False, 0)
