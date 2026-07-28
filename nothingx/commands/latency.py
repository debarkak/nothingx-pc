from ..wire import Cmd, Dir


class LatencyCommands:
    def __init__(self, session):
        self._s = session

    def get(self) -> bool:
        pkt = self._s.run(Cmd.LATENCY_GET, Dir.GET, b"")
        # 0x01 = on, 0x02 = off
        return pkt.payload == b"\x01" if pkt else False

    def set(self, enable: bool):
        payload = b"\x01" if enable else b"\x02"
        self._s.run(Cmd.LATENCY_SET, Dir.SET, payload)
