from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.enums import OrderRole, OrderStatus, OrderType

if TYPE_CHECKING:
    import pandas as pd


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
    valid_from_bars: int | None = None
    valid_until_bars: int | None = None
    stop_triggered: bool = False
    child_orders: list[Order] = field(default_factory=list)
    parent_order: Order | None = field(default=None, repr=False, compare=False)

    # TODO: add more validity checks here (e.g., order_type-specific price requirements)
    def __post_init__(self) -> None:
        if (
            self.valid_from_time is not None
            and self.valid_until_time is not None
            and self.valid_from_time > self.valid_until_time
        ):
            raise ValueError("An order's valid_from_time cannot be after its valid_until_time.")
        if (
            self.valid_from_bars is not None
            and self.valid_until_bars is not None
            and self.valid_from_bars > self.valid_until_bars
        ):
            raise ValueError("An order's valid_from_bars cannot be after its valid_until_bars.")
        if self.valid_from_time is not None and self.valid_from_bars is not None:
            raise ValueError("An order cannot have both valid_from_time and valid_from_bars set.")
        if self.valid_until_time is not None and self.valid_until_bars is not None:
            raise ValueError("An order cannot have both valid_until_time and valid_until_bars set.")

    def is_scheduled_at(self, bar_time: pd.Timestamp) -> bool:
        return self.valid_from_time is not None and self.valid_from_time > bar_time

    def has_expired_at(self, bar_time: pd.Timestamp) -> bool:
        return self.valid_until_time is not None and self.valid_until_time < bar_time
