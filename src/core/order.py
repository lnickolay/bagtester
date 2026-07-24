from __future__ import annotations

from dataclasses import dataclass

from core.enums import OrderDirection, OrderType


@dataclass
class Order:

    ticker: str
    direction: OrderDirection
    order_type: OrderType
    size: float
