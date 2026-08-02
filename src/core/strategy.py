from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.enums import OrderRole, OrderType
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

    def buy(
        self,
        size: float | None = None,
        tp_price: float | None = None,
        sl_price: float | None = None,
        order_ttl_bars: int | None = None,
        position_ttl_bars: int | None = None,
    ) -> None:
        price = self.get_price("Close")
        if sl_price is not None and sl_price >= price:
            raise ValueError(f"SL {sl_price} must be below entry {price} for BUY.")
        if tp_price is not None and tp_price <= price:
            raise ValueError(f"TP {tp_price} must be above entry {price} for BUY.")
        self._place_order(size, tp_price, sl_price, 1, order_ttl_bars, position_ttl_bars)

    def sell(
        self,
        size: float | None = None,
        tp_price: float | None = None,
        sl_price: float | None = None,
        order_ttl_bars: int | None = None,
        position_ttl_bars: int | None = None,
    ) -> None:
        price = self.get_price("Close")
        if sl_price is not None and sl_price <= price:
            raise ValueError(f"SL {sl_price} must be above entry {price} for SELL.")
        if tp_price is not None and tp_price >= price:
            raise ValueError(f"TP {tp_price} must be below entry {price} for SELL.")
        self._place_order(size, tp_price, sl_price, -1, order_ttl_bars, position_ttl_bars)

    def _place_order(
        self,
        size: float | None,
        tp_price: float | None,
        sl_price: float | None,
        sign: int,
        order_ttl_bars: int | None,
        position_ttl_bars: int | None,
    ) -> None:
        price = self.get_price("Close")
        if size is None:
            size = self.sizer.calc_order_size(price, self.broker.equity, sl_price)
        signed_size = sign * size
        order = Order(
            ticker=self._current_ticker,
            order_type=OrderType.MARKET,
            size=signed_size,
            valid_until_bars=order_ttl_bars,
        )

        if tp_price is not None:
            order.child_orders.append(
                Order(
                    ticker=self._current_ticker,
                    order_type=OrderType.LIMIT,
                    size=-signed_size,
                    role=OrderRole.TAKE_PROFIT,
                    limit_price=tp_price,
                    parent_order=order,
                )
            )
        if sl_price is not None:
            order.child_orders.append(
                Order(
                    ticker=self._current_ticker,
                    order_type=OrderType.STOP,
                    size=-signed_size,
                    role=OrderRole.STOP_LOSS,
                    stop_price=sl_price,
                    parent_order=order,
                )
            )
        if position_ttl_bars is not None:
            order.child_orders.append(
                Order(
                    ticker=self._current_ticker,
                    order_type=OrderType.MARKET,
                    size=-signed_size,
                    valid_from_bars=position_ttl_bars,
                    parent_order=order,
                )
            )
        self.broker.submit_order(order)

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
