import time
from ..wire import Cmd, Dir
from ..responses import Parsers, FitTestResult
from ..session import _StreamParser
from ..errors import TimeoutError, NothingError


class FitCommands:
    def __init__(self, session, device_name: str = ""):
        self._s = session
        self._device_name = device_name

    @property
    def is_supported(self) -> bool:
        name = self._device_name.lower()
        if "cmf" in name:
            return False
        return True

    def run(self, timeout=10.0, step_callback=None) -> FitTestResult:
        if not self.is_supported:
            raise NothingError(f"eartip fit test is not supported on {self._device_name or 'this device'}")

        # send the start command and wait for the ACK
        self._s.send(Cmd.FIT_TEST, Dir.SET, b"\x01")
        try:
            self._s.recv(timeout=2.0)
        except Exception:
            pass

        # now listen for the unsolicited result packet (dir=0xE0, cmd=0x0D)
        self._s._conn.sock.settimeout(0.1)
        parser = _StreamParser()
        deadline = time.time() + timeout

        while time.time() < deadline:
            if step_callback:
                step_callback()
                
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

        raise TimeoutError(f"Timed out waiting for fit test result — make sure both earbuds are in your ears and your model ({self._device_name or 'device'}) supports fit testing.")
