import time
import logging
from typing import Optional
from dataclasses import dataclass

from .scanner import RFCOMMConnection
from .wire import build_packet, crc16, Dir
from .errors import TimeoutError

log = logging.getLogger(__name__)


@dataclass
class Packet:
    cmd: int
    direction: int
    op_id: int
    payload: bytes
    raw: bytes

    def __str__(self):
        return f"Packet(cmd=0x{self.cmd:02X} dir=0x{self.direction:02X} op={self.op_id} len={len(self.payload)} hex={self.raw.hex()})"


class _StreamParser:
    def __init__(self):
        self._buf = bytearray()

    def feed(self, data: bytes):
        self._buf.extend(data)

    def next(self) -> Optional[Packet]:
        while len(self._buf) >= 8:
            idx = self._buf.find(0x55)
            if idx == -1:
                self._buf.clear()
                return None
            if idx > 0:
                del self._buf[:idx]
            if len(self._buf) < 8:
                return None

            b1, b2 = self._buf[1], self._buf[2]
            standard    = b1 == 0x60 and b2 == 0x01
            unsolicited = b1 == 0x00 and b2 == 0x01

            if not (standard or unsolicited):
                del self._buf[0]
                continue

            plen  = self._buf[5]
            total = 8 + plen + (2 if standard else 0)

            if len(self._buf) < total:
                return None

            raw = self._buf[:total]

            if standard:
                got  = bytes(raw[-2:])
                want = crc16(bytes(raw[:-2]))
                if got != want:
                    log.warning(f"CRC mismatch: got {got.hex()} want {want.hex()}")
                    del self._buf[0]
                    continue

            del self._buf[:total]
            return Packet(
                cmd=raw[3],
                direction=raw[4],
                op_id=raw[7],
                payload=bytes(raw[8:8 + plen]),
                raw=bytes(raw),
            )
        return None


class Session:
    def __init__(self, conn: RFCOMMConnection):
        self._conn = conn
        self._parser = _StreamParser()

    def send(self, cmd: int, direction: int, payload: bytes, op_id: int = 1):
        raw = build_packet(cmd, direction, list(payload), op_id)
        self._conn.send(raw)

    def recv(self, timeout: float = 2.0) -> Packet:
        deadline = time.time() + timeout
        while time.time() < deadline:
            pkt = self._parser.next()
            if pkt:
                return pkt
            self._conn.sock.settimeout(0.3)
            data = self._conn.recv(1024)
            if data:
                self._parser.feed(data)
        raise TimeoutError(f"no packet received in {timeout}s")

    def run(self, cmd: int, direction: int, payload: bytes, timeout: float = 2.0) -> Packet:
        self.send(cmd, direction, payload)
        deadline = time.time() + timeout
        while time.time() < deadline:
            pkt = self.recv(deadline - time.time())
            if pkt.direction in (Dir.ACK, Dir.RESPONSE):
                return pkt
        raise TimeoutError(f"no response to cmd 0x{cmd:02X} in {timeout}s")
