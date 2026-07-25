from __future__ import annotations

from dataclasses import dataclass

from core.enums import OrderType


@dataclass
class Order:

    ticker: str
    order_type: OrderType
    size: float
