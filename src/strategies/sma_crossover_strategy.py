from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from core.enums import OrderDirection
from core.order import OrderType
from core.sizer import EquityRatioSizer
from core.strategy import Strategy

if TYPE_CHECKING:
    from core.broker import Broker
    from core.context import Context


class SMACrossoverStrategy(Strategy):

    _sma_short_period: int
    _sma_long_period: int

    def __init__(
        self,
        broker: Broker,
        sma_short_period: int = 20,
        sma_long_period: int = 50,
        pos_size_ratio: float = 0.1,
    ) -> None:
        super().__init__(broker)
        self._sma_short_period = sma_short_period
        self._sma_long_period = sma_long_period
        self.sizer = EquityRatioSizer(pos_size_ratio)

    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        sma_data = {}
        for ticker, ticker_price_data in price_data.items():
            sma_short_series = ticker_price_data["Close"].rolling(self._sma_short_period).mean()
            sma_long_series = ticker_price_data["Close"].rolling(self._sma_long_period).mean()
            sma_data[ticker] = pd.DataFrame(
                {
                    "SMAShort": sma_short_series,
                    "SMALong": sma_long_series,
                }
            )
        return sma_data

    # TODO
    def pre_open(self, context: Context) -> None:
        for ticker in context.get_tickers():
            s_is_over_l = context.get_indicator(ticker, "SMAShort") > context.get_indicator(ticker, "SMALong")
            s_was_over_l = context.get_indicator(ticker, "SMAShort", 1) > context.get_indicator(ticker, "SMALong", 1)
            crossed_over = s_is_over_l and not s_was_over_l
            crossed_under = not s_is_over_l and s_was_over_l

            price = context.get_price(ticker, "Close")
            size = self.sizer.calc_order_size(price, self.broker.equity, None)
            if self.broker.get_position(ticker) is not None:
                size *= 2

            if crossed_over:
                self.create_order(ticker, OrderDirection.BUY, OrderType.MARKET, size)
            elif crossed_under:
                self.create_order(ticker, OrderDirection.SELL, OrderType.MARKET, size)

    def pre_close(self, context: Context) -> None:
        pass
