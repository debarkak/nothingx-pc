import time
from ..wire import Cmd, Dir
from ..responses import Parsers, FitTestResult
from ..session import _StreamParser


class FitCommands:
    def __init__(self, session):
        self._s = session

    def run(self, timeout=10.0) -> FitTestResult:
        # send the start command and wait for the ACK
        self._s.send(Cmd.FIT_TEST, Dir.SET, b"\x01")
        try:
            self._s.recv(timeout=2.0)
        except Exception:
            pass

        # now listen for the unsolicited result packet (dir=0xE0, cmd=0x0D)
        self._s._conn.sock.settimeout(0.3)
        parser = _StreamParser()
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                data = self._s._conn.recv(4096)
                if data:
                    parser.feed(data)
            except OSError:
                pass

            while True:
                pkt = parser.next()
                if pkt is None:
                    break
                if pkt.cmd == Cmd.FIT_RESULT:
                    return Parsers.fit_result(pkt.payload)

        raise TimeoutError("Timed out waiting for fit test result — are both earbuds in your ears?")
