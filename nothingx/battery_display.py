from typing import Optional


def battery_percent(value: Optional[int]) -> str:
    """Format a battery reading without treating 0% as missing."""
    return "--%" if value is None else f"{value}%"
