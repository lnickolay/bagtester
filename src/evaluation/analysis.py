from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from evaluation.history import History


class Analysis:

    series: pd.DataFrame

    opened_position_count: int
    closed_position_count: int

    duration_years: float

    cagr: float
    max_drawdown: float

    def __init__(self, history: History, bar_timeline: pd.DatetimeIndex, initial_cash: float) -> None:
        self.series = self._initialize_series(history, bar_timeline, initial_cash)
        self._calc_derived_series()
        self._calc_stats_and_metrics(history)

    def _initialize_series(self, history: History, bar_timeline: pd.DatetimeIndex, initial_cash: float) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "equity": np.concatenate(([initial_cash], history.equity_series)),
                "cash": np.concatenate(([initial_cash], history.cash_series)),
                "gross_exposure": np.concatenate(([0.0], history.gross_exposure_series)),
                "long_exposure": np.concatenate(([0.0], history.long_exposure_series)),
                "short_exposure": np.concatenate(([0.0], history.short_exposure_series)),
            },
            index=bar_timeline.insert(0, bar_timeline[0]),
        )

    def _calc_derived_series(self) -> None:
        running_max_series = self.series["equity"].cummax()
        self.series["drawdown"] = (self.series["equity"] - running_max_series) / running_max_series

    def _calc_stats_and_metrics(self, history: History) -> None:
        self.opened_position_count = sum(len(ticker_trades) for ticker_trades in history.trades.values())
        self.closed_position_count = self.opened_position_count - len(history.open_trades)

        start_time = self.series.index[0]
        end_time = self.series.index[-1]
        start_equity = self.series["equity"].iloc[0]
        end_equity = self.series["equity"].iloc[-1]

        # TODO: possibly add constants for days per year, seconds per day etc
        self.duration_years = pd.Timedelta(end_time - start_time).total_seconds() / (365.2425 * 24 * 60 * 60)
        self.cagr = ((end_equity / start_equity) ** (1 / self.duration_years)) - 1.0
        self.max_drawdown = self.series["drawdown"].min()
