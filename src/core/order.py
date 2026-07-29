from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.enums import OrderRole, OrderStatus, OrderType


@dataclass
class Order:

    ticker: str
    order_type: OrderType
    size: float
    status: OrderStatus = OrderStatus.SUBMITTED
    role: OrderRole = OrderRole.STANDARD
    stop_price: float | None = None
    limit_price: float | None = None
    valid_from_time: pd.Timestamp | None = None
    valid_until_time: pd.Timestamp | None = None
    stop_triggered: bool = False
    child_orders: list[Order] = field(default_factory=list)
    parent_order: Order | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (
            self.valid_from_time is not None
            and self.valid_until_time is not None
            and self.valid_from_time > self.valid_until_time
        ):
            raise ValueError("An order's valid_from_time cannot be after its valid_until_time.")

    def is_scheduled_at(self, bar_time: pd.Timestamp) -> bool:
        return self.valid_from_time is not None and self.valid_from_time > bar_time

    def has_expired_at(self, bar_time: pd.Timestamp) -> bool:
        return self.valid_until_time is not None and self.valid_until_time < bar_time
