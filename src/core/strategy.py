from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.order import Order

if TYPE_CHECKING:
    import pandas as pd

    from core.broker import Broker
    from core.context import Context
    from core.enums import OrderDirection
    from core.exit_rule_spec import ExitRuleSpec
    from core.order import OrderType
    from core.sizer import Sizer


class Strategy(ABC):

    broker: Broker
    sizer: Sizer

    # TODO: strategy probably shouldn't need to know broker
    def __init__(self, broker: Broker) -> None:
        self.broker = broker

    def create_order(
        self,
        ticker: str,
        direction: OrderDirection,
        order_type: OrderType,
        size: float,
        stop_loss_specs: list[ExitRuleSpec] | None = None,
        take_profit_specs: list[ExitRuleSpec] | None = None,
        timed_exit_specs: list[ExitRuleSpec] | None = None,
    ) -> None:
        order = Order(
            ticker=ticker,
            direction=direction,
            order_type=order_type,
            size=size,
            stop_loss_specs=stop_loss_specs or [],
            take_profit_specs=take_profit_specs or [],
            timed_exit_specs=timed_exit_specs or [],
        )
        self.broker.submit_order(order)

    # TODO: also pass start and end timestamps as arguments here so that no time is wasted on computing indicator values
    # that are not actually needed?
    @abstractmethod
    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        pass

    @abstractmethod
    def pre_open(self, context: Context) -> None:
        pass

    @abstractmethod
    def pre_close(self, context: Context) -> None:
        pass
