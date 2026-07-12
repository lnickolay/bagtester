from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.enums import OrderDirection, OrderType

if TYPE_CHECKING:
    from core.exit_rule_spec import ExitRuleSpec


@dataclass
class Order:

    ticker: str
    direction: OrderDirection
    order_type: OrderType
    size: float
    # TODO: use tuples here instead of lists?
    stop_loss_specs: list[ExitRuleSpec] = field(default_factory=list)
    take_profit_specs: list[ExitRuleSpec] = field(default_factory=list)
    timed_exit_specs: list[ExitRuleSpec] = field(default_factory=list)
