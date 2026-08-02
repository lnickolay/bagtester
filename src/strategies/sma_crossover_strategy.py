from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from core.sizer import EquityRatioSizer
from core.strategy import Strategy

if TYPE_CHECKING:
    from core.broker import Broker


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

    def process_ticker(self) -> None:
        s_is_over_l = self.get_indicator("SMAShort") > self.get_indicator("SMALong")
        s_was_over_l = self.get_indicator("SMAShort", bars_back=1) > self.get_indicator("SMALong", bars_back=1)
        crossed_over = s_is_over_l and not s_was_over_l
        crossed_under = not s_is_over_l and s_was_over_l

        if crossed_over:
            self.close()
            self.buy()
        elif crossed_under:
            self.close()
            self.sell()
