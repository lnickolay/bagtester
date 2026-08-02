from __future__ import annotations

from typing import TYPE_CHECKING

from core.sizer import EquityRatioSizer
from core.strategy import Strategy

if TYPE_CHECKING:
    import pandas as pd

    from core.broker import Broker


# this strat currently needs to look ahead one bar to decide whether to enter the market at the open of bar N depending
# on the open price at bar N; there is currently no other way to simulate this and it doesn't induce true lookahead bias
class ShortTheGapStrategy(Strategy):

    _min_gap_up_ratio: float
    _stop_loss_ratio: float
    _max_short_exposure_ratio: float
    _max_concurrent_trades: int

    def __init__(
        self,
        broker: Broker,
        min_gap_up_ratio: float = 0.1,
        stop_loss_ratio: float = 0.05,
        pos_size_ratio: float = 0.1,
    ) -> None:
        super().__init__(broker)
        self._min_gap_up_ratio = min_gap_up_ratio
        self._stop_loss_ratio = stop_loss_ratio
        self.sizer = EquityRatioSizer(pos_size_ratio)

    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        gap_up_ratio_data = {}
        for ticker, ticker_price_data in price_data.items():
            ticker_gap_up_ratio_series = ticker_price_data["Open"].shift(-1) / ticker_price_data["Close"] - 1.0
            gap_up_ratio_data[ticker] = ticker_gap_up_ratio_series.to_frame(name="GapUpRatio")
        return gap_up_ratio_data

    def process_ticker(self) -> None:
        if self.get_indicator("GapUpRatio") >= self._min_gap_up_ratio:
            sl_price = (1.0 + self._stop_loss_ratio) * self.get_price("Open", -1)
            self.sell(sl_price=sl_price, position_ttl_bars=0)
