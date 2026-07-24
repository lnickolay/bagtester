from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.enums import OrderDirection, PositionSide

if TYPE_CHECKING:
    import pandas as pd

    from core.order import Order


@dataclass
class Position:

    ticker: str
    side: PositionSide
    size: float
    entry_price: float
    entry_bar_time: pd.Timestamp
    entry_bar_pos: int
    # stop_loss_rules: list[ExitRule] = field(default_factory=list)
    # take_profit_rules: list[ExitRule] = field(default_factory=list)
    # timed_exit_rules: list[ExitRule] = field(default_factory=list)

    @classmethod
    def from_order(cls, order: Order, entry_price: float, entry_bar_time: pd.Timestamp, entry_bar_pos: int) -> Position:
        side = PositionSide.LONG if order.direction == OrderDirection.BUY else PositionSide.SHORT
        return cls(
            ticker=order.ticker,
            side=side,
            size=order.size,
            entry_price=entry_price,
            entry_bar_time=entry_bar_time,
            entry_bar_pos=entry_bar_pos,
        )
