from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import pandas as pd

    from core.order import Order


@dataclass
class Position:

    ticker: str
    size: float
    entry_price: float
    entry_bar_time: pd.Timestamp
    entry_bar_pos: int

    @classmethod
    def from_order(cls, order: Order, entry_price: float, entry_bar_time: pd.Timestamp, entry_bar_pos: int) -> Position:
        return cls(
            ticker=order.ticker,
            size=order.size,
            entry_price=entry_price,
            entry_bar_time=entry_bar_time,
            entry_bar_pos=entry_bar_pos,
        )
