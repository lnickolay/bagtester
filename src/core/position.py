from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.enums import OrderDirection, PositionSide
from core.exit_rule import ExitRule

if TYPE_CHECKING:
    import pandas as pd

    from core.order import Order


@dataclass
class Position:

    ticker: str
    side: PositionSide
    size: float
    initial_size: float
    size_pct: float
    entry_price: float
    entry_bar_time: pd.Timestamp
    entry_bar_pos: int
    # TODO: use tuples here instead of lists?
    stop_loss_rules: list[ExitRule] = field(default_factory=list)
    take_profit_rules: list[ExitRule] = field(default_factory=list)
    timed_exit_rules: list[ExitRule] = field(default_factory=list)

    @classmethod
    def from_order(cls, order: Order, entry_price: float, entry_bar_time: pd.Timestamp, entry_bar_pos: int) -> Position:
        side = PositionSide.LONG if order.direction == OrderDirection.BUY else PositionSide.SHORT
        # generate new position object first (the position object is needed for exit rule generation)
        position = cls(
            ticker=order.ticker,
            side=side,
            size=order.size,
            initial_size=order.size,
            size_pct=1.0,
            entry_price=entry_price,
            entry_bar_time=entry_bar_time,
            entry_bar_pos=entry_bar_pos,
        )
        # generate exit rules from specs and add them to the appropriate lists
        for spec in order.stop_loss_specs:
            position.stop_loss_rules.append(ExitRule.from_spec(spec, position))
        for spec in order.take_profit_specs:
            position.take_profit_rules.append(ExitRule.from_spec(spec, position))
        for spec in order.timed_exit_specs:
            position.timed_exit_rules.append(ExitRule.from_spec(spec, position))

        return position
