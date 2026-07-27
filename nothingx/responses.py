from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BatteryStatus:
    left: int
    right: int
    case: Optional[int] = field(default=None)  # None if case isn't reporting


@dataclass
class AncState:
    mode: int


@dataclass
class FitTestResult:
    # 0 = good seal, 1 = poor seal, 2 = not in ear
    left: int
    right: int

    GOOD       = 0
    POOR       = 1
    NOT_IN_EAR = 2

    @property
    def left_ok(self):
        return self.left == 0

    @property
    def right_ok(self):
        return self.right == 0

    def _label(self, code):
        return {0: "✓ Good seal", 1: "✗ Poor seal", 2: "✗ Not in ear"}.get(code, f"✗ Unknown ({code})")

    def summary(self):
        return f"Left: {self._label(self.left)}  Right: {self._label(self.right)}"


class Parsers:
    @staticmethod
    def battery(payload: bytes) -> BatteryStatus:
        left = right = 0
        case = None
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

    @staticmethod
    def fit_result(payload: bytes) -> FitTestResult:
        # payload[0] = left result, payload[1] = right result
        left  = payload[0] if len(payload) > 0 else FitTestResult.NOT_IN_EAR
        right = payload[1] if len(payload) > 1 else FitTestResult.NOT_IN_EAR
        return FitTestResult(left=left, right=right)
