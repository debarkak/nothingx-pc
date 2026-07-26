from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BatteryStatus:
    left: int
    right: int
    case: Optional[int] = field(default=None)  # present when case is in-range and lid state is known


@dataclass
class AncState:
    mode: int


class Parsers:
    @staticmethod
    def battery(payload: bytes) -> BatteryStatus:
        left = right = 0
        case: Optional[int] = None
        i = 1
        while i < len(payload) - 1:
            tag, val = payload[i], payload[i + 1]
            if tag == 0x02:
                left = val
            elif tag == 0x03:
                right = val
            elif tag == 0x04:
                case = val
            i += 2
        return BatteryStatus(left=left, right=right, case=case)

    @staticmethod
    def firmware(payload: bytes) -> str:
        return payload.decode("ascii", errors="ignore")

    @staticmethod
    def anc_state(payload: bytes) -> int:
        return payload[1] if len(payload) >= 2 else 0
