from __future__ import annotations

from typing import TYPE_CHECKING

from core.enums import BarSubstep, OrderDirection
from core.exit_rule_spec import StopLossRatioSpec, TimedExitSpec
from core.order import OrderType
from core.strategy import Strategy

if TYPE_CHECKING:
    import pandas as pd

    from core.broker import Broker
    from core.context import Context


class ShortTheGapStrategy(Strategy):

    _min_gap_up_pct: float
    _stop_loss_pct: float
    _pos_size_pct: float
    _max_short_exposure_pct: float
    _max_concurrent_trades: int

    def __init__(
        self,
        broker: Broker,
        # TODO: suffixed _pct but hold ratios
        min_gap_up_pct: float = 0.5,
        stop_loss_pct: float = 0.2,
        pos_size_pct: float = 0.1,
        max_short_exposure_pct: float = 0.4,
    ) -> None:
        super().__init__(broker)
        self._min_gap_up_pct = min_gap_up_pct
        self._stop_loss_pct = stop_loss_pct
        self._pos_size_pct = pos_size_pct
        self._max_short_exposure_pct = max_short_exposure_pct

        self._max_concurrent_trades = int(max_short_exposure_pct / pos_size_pct)

    def initialize(self, price_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        gap_up_pct_data = {}
        for ticker, ticker_price_data in price_data.items():
            ticker_gap_up_pct_series = ticker_price_data["Open"] / ticker_price_data["Close"].shift(1) - 1.0
            gap_up_pct_data[ticker] = ticker_gap_up_pct_series.to_frame(name="GapUpPct")
        return gap_up_pct_data

    def pre_open(self, context: Context) -> None:
        candidates = []
        for ticker in context.get_tickers():
            gap_up_pct = context.get_indicator(ticker, "GapUpPct")
            if gap_up_pct >= self._min_gap_up_pct:
                candidates.append((ticker, gap_up_pct))

        candidates.sort(key=lambda x: x[1], reverse=True)

        for ticker in [candidate[0] for candidate in candidates[: self._max_concurrent_trades]]:
            sell_price = context.get_price(ticker, "Open")
            size = self.broker.equity * self._pos_size_pct / sell_price

            stop_loss_spec = StopLossRatioSpec(self._stop_loss_pct)
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
