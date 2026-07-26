from dataclasses import dataclass


@dataclass
class BatteryStatus:
    left: int
    right: int


@dataclass
class AncState:
    mode: int


class Parsers:
    @staticmethod
    def battery(payload: bytes) -> BatteryStatus:
        left = right = 0
        i = 1
        while i < len(payload) - 1:
            tag, val = payload[i], payload[i + 1]
            if tag == 0x02:
                left = val
            elif tag == 0x03:
                right = val
            i += 2
        return BatteryStatus(left=left, right=right)

    @staticmethod
    def firmware(payload: bytes) -> str:
        return payload.decode("ascii", errors="ignore")

    @staticmethod
    def anc_state(payload: bytes) -> int:
        return payload[1] if len(payload) >= 2 else 0
