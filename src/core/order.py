from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.enums import OrderRole, OrderStatus, OrderType


@dataclass
class Order:

    ticker: str
    order_type: OrderType
    size: float
    status: OrderStatus = OrderStatus.ACCEPTED
    role: OrderRole | None = None
    stop_price: float | None = None
    limit_price: float | None = None
    valid_from_time: pd.Timestamp | None = None
    valid_until_time: pd.Timestamp | None = None
    stop_triggered: bool = False
    child_orders: list[Order] = field(default_factory=list)
    parent_order: Order | None = field(default=None, repr=False, compare=False)
