from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.enums import OrderType
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
        price = self.get_price("Close")
        if sl_price is not None and sl_price >= price:
            raise ValueError(f"SL {sl_price} must be below entry {price} for BUY.")
        if tp_price is not None and tp_price <= price:
            raise ValueError(f"TP {tp_price} must be above entry {price} for BUY.")
        if size is None:
            size = self.sizer.calc_order_size(price, self.broker.equity, sl_price)
        self.broker.submit_order(Order(self._current_ticker, OrderType.MARKET, size))

    def sell(self, size: float | None = None, tp_price: float | None = None, sl_price: float | None = None) -> None:
        price = self.get_price("Close")
        if sl_price is not None and sl_price <= price:
            raise ValueError(f"SL {sl_price} must be above entry {price} for SELL.")
        if tp_price is not None and tp_price >= price:
            raise ValueError(f"TP {tp_price} must be below entry {price} for SELL.")
        if size is None:
            size = self.sizer.calc_order_size(price, self.broker.equity, sl_price)
        self.broker.submit_order(Order(self._current_ticker, OrderType.MARKET, -size))

    def close(self) -> None:
        pos = self.broker.get_position(self._current_ticker)
        if pos is None:
            return
        self.broker.submit_order(Order(self._current_ticker, OrderType.MARKET, -pos.size))

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
