from decimal import Decimal

def to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)

def round_one_decimal(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 1)
