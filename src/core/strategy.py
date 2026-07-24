from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.enums import OrderDirection, OrderType
from core.order import Order

if TYPE_CHECKING:
    import pandas as pd

    from core.broker import Broker
    from core.context import Context
    from core.sizer import Sizer


class Strategy(ABC):

    broker: Broker
    sizer: Sizer

    def __init__(self, broker: Broker) -> None:
        self.broker = broker

    # TODO: check if ticker can be made implicit
    # TODO: concrete strategy should not have to call self.sizer manually
    def buy(self, size: float, ticker: str) -> None:
        order = Order(ticker=ticker, direction=OrderDirection.BUY, order_type=OrderType.MARKET, size=size)
        self.broker.submit_order(order)

    def sell(self, size: float, ticker: str) -> None:
        order = Order(ticker=ticker, direction=OrderDirection.SELL, order_type=OrderType.MARKET, size=size)
        self.broker.submit_order(order)

    def close(self, ticker: str) -> None:
        pass

    # def create_order(
    #     self,
    #     ticker: str,
    #     direction: OrderDirection,
    #     order_type: OrderType,
    #     size: float,
    #     stop_loss_specs: list[ExitRuleSpec] | None = None,
    #     take_profit_specs: list[ExitRuleSpec] | None = None,
    #     timed_exit_specs: list[ExitRuleSpec] | None = None,
    # ) -> None:
    #     order = Order(
    #         ticker=ticker,
    #         direction=direction,
    #         order_type=order_type,
    #         size=size,
    #         stop_loss_specs=stop_loss_specs or [],
    #         take_profit_specs=take_profit_specs or [],
    #         timed_exit_specs=timed_exit_specs or [],
    #     )
    #     self.broker.submit_order(order)

    @abstractmethod
    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        pass

    @abstractmethod
    def process_ticker(self, context: Context) -> None:
        pass

    # @abstractmethod
    # def pre_open(self, context: Context) -> None:
    #     pass

    # @abstractmethod
    # def pre_close(self, context: Context) -> None:
    #     pass
