from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.enums import OrderDirection, OrderType, PositionSide
from core.order import Order

if TYPE_CHECKING:
    import pandas as pd

    from core.broker import Broker
    from core.context import Context
    from core.sizer import Sizer


class Strategy(ABC):

    broker: Broker
    sizer: Sizer
    _context: Context
    _current_ticker: str

    def __init__(self, broker: Broker) -> None:
        self.broker = broker

    def buy(self, size: float | None = None, tp_price: float | None = None, sl_price: float | None = None) -> None:
        if size is None:
            size = self.sizer.calc_order_size(self.get_price("Close"), self.broker.equity, sl_price)
        order = Order(self._current_ticker, OrderDirection.BUY, OrderType.MARKET, size)
        self.broker.submit_order(order)

    def sell(self, size: float | None = None, tp_price: float | None = None, sl_price: float | None = None) -> None:
        if size is None:
            size = self.sizer.calc_order_size(self.get_price("Close"), self.broker.equity, sl_price)
        order = Order(self._current_ticker, OrderDirection.SELL, OrderType.MARKET, size)
        self.broker.submit_order(order)

    def close(self) -> None:
        pos = self.broker.get_position(self._current_ticker)
        if pos is None:
            return

        direction = OrderDirection.BUY if pos.side == PositionSide.SHORT else OrderDirection.SELL
        order = Order(self._current_ticker, direction, OrderType.MARKET, pos.size)
        self.broker.submit_order(order)

    def get_price(self, col: str, bars_back: int = 0) -> float:
        return self._context.get_price(col, self._current_ticker, bars_back)

    def get_indicator(self, col: str, bars_back: int = 0) -> float:
        return self._context.get_indicator(col, self._current_ticker, bars_back)

    def process(self, context: Context) -> None:
        self._context = context
        for ticker in context.price_data:
            self._current_ticker = ticker
            self.process_ticker()

    @abstractmethod
    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        pass

    @abstractmethod
    def process_ticker(self) -> None:
        pass
