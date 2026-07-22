from __future__ import annotations

from typing import TYPE_CHECKING

from core.enums import BarSubstep, OrderDirection
from core.exit_rule_spec import StopLossRatioSpec, TimedExitSpec
from core.order import OrderType
from core.sizer import EquityRatioSizer
from core.strategy import Strategy

if TYPE_CHECKING:
    import pandas as pd

    from core.broker import Broker
    from core.context import Context


class ShortTheGapStrategy(Strategy):

    _min_gap_up_ratio: float
    _stop_loss_ratio: float
    _max_short_exposure_ratio: float
    _max_concurrent_trades: int

    def __init__(
        self,
        broker: Broker,
        min_gap_up_ratio: float = 0.5,
        stop_loss_ratio: float = 0.2,
        pos_size_ratio: float = 0.1,
        max_short_exposure_ratio: float = 0.4,
    ) -> None:
        super().__init__(broker)
        self._min_gap_up_ratio = min_gap_up_ratio
        self._stop_loss_ratio = stop_loss_ratio
        self.sizer = EquityRatioSizer(pos_size_ratio)
        self._max_short_exposure_ratio = max_short_exposure_ratio

        self._max_concurrent_trades = int(max_short_exposure_ratio / pos_size_ratio)

    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        gap_up_ratio_data = {}
        for ticker, ticker_price_data in price_data.items():
            ticker_gap_up_ratio_series = ticker_price_data["Open"] / ticker_price_data["Close"].shift(1) - 1.0
            gap_up_ratio_data[ticker] = ticker_gap_up_ratio_series.to_frame(name="GapUpRatio")
        return gap_up_ratio_data

    def pre_open(self, context: Context) -> None:
        candidates = []
        for ticker in context.get_tickers():
            gap_up_ratio = context.get_indicator(ticker, "GapUpRatio")
            if gap_up_ratio >= self._min_gap_up_ratio:
                candidates.append((ticker, gap_up_ratio))

        candidates.sort(key=lambda x: x[1], reverse=True)

        for ticker in [candidate[0] for candidate in candidates[: self._max_concurrent_trades]]:
            sell_price = context.get_price(ticker, "Open")
            size = self.sizer.calc_order_size(sell_price, self.broker.equity, None)

            stop_loss_spec = StopLossRatioSpec(self._stop_loss_ratio)
            timed_exit_spec = TimedExitSpec(0, evaluated_substeps=(BarSubstep.CLOSE,))
            self.create_order(
                ticker,
                OrderDirection.SELL,
                OrderType.MARKET,
                size,
                stop_loss_specs=[stop_loss_spec],
                timed_exit_specs=[timed_exit_spec],
            )

    def pre_close(self, context: Context) -> None:
        pass
