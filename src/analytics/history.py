from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from analytics.broker_observer import BrokerObserver

if TYPE_CHECKING:
    from analytics.snapshots import AccountSnapshot


class History(BrokerObserver):

    _bar_timeline: pd.DatetimeIndex

    _initial_cash: float
    _equity_series: np.ndarray
    _cash_series: np.ndarray
    _gross_exposure_series: np.ndarray
    _long_exposure_series: np.ndarray
    _short_exposure_series: np.ndarray

    total_margin_interest_cost: float
    total_asset_borrow_cost: float

    account_history: pd.DataFrame

    def __init__(self, bar_timeline: pd.DatetimeIndex, initial_cash: float) -> None:
        self._bar_timeline = bar_timeline
        bar_count = len(bar_timeline)

        self._initial_cash = initial_cash
        self._equity_series = np.empty(bar_count)
        self._cash_series = np.empty(bar_count)
        self._gross_exposure_series = np.empty(bar_count)
        self._long_exposure_series = np.empty(bar_count)
        self._short_exposure_series = np.empty(bar_count)

        self.total_margin_interest_cost = 0.0
        self.total_asset_borrow_cost = 0.0

    def on_account_snapshot(self, snapshot: AccountSnapshot, bar_num: int) -> None:
        self._equity_series[bar_num] = snapshot.equity
        self._cash_series[bar_num] = snapshot.cash
        self._gross_exposure_series[bar_num] = snapshot.gross_exposure
        self._long_exposure_series[bar_num] = snapshot.long_exposure
        self._short_exposure_series[bar_num] = snapshot.short_exposure

        self.total_margin_interest_cost += snapshot.margin_interest_cost
        self.total_asset_borrow_cost += snapshot.asset_borrow_cost

    def finalize(self) -> None:
        self.account_history = pd.DataFrame(
            {
                "equity": np.concatenate(([self._initial_cash], self._equity_series)),
                "cash": np.concatenate(([self._initial_cash], self._cash_series)),
                "gross_exposure": np.concatenate(([0.0], self._gross_exposure_series)),
                "long_exposure": np.concatenate(([0.0], self._long_exposure_series)),
                "short_exposure": np.concatenate(([0.0], self._short_exposure_series)),
            },
            index=self._bar_timeline.insert(0, self._bar_timeline[0]),
        )
