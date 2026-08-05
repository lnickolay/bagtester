from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from core.broker_observer import BrokerObserver

if TYPE_CHECKING:
    from core.events import AccountSnapshot
    from core.position import Position


class History(BrokerObserver):

    equity_series: np.ndarray
    cash_series: np.ndarray
    gross_exposure_series: np.ndarray
    long_exposure_series: np.ndarray
    short_exposure_series: np.ndarray

    total_margin_interest_cost: float
    total_asset_borrow_cost: float

    positions: list[Position]

    def __init__(self, bar_count: int) -> None:
        self.equity_series = np.empty(bar_count)
        self.cash_series = np.empty(bar_count)
        self.gross_exposure_series = np.empty(bar_count)
        self.long_exposure_series = np.empty(bar_count)
        self.short_exposure_series = np.empty(bar_count)

        self.total_margin_interest_cost = 0.0
        self.total_asset_borrow_cost = 0.0

        self.positions = []

    def on_account_snapshot(self, snapshot: AccountSnapshot, bar_num: int) -> None:
        self.equity_series[bar_num] = snapshot.equity
        self.cash_series[bar_num] = snapshot.cash
        self.gross_exposure_series[bar_num] = snapshot.gross_exposure
        self.long_exposure_series[bar_num] = snapshot.long_exposure
        self.short_exposure_series[bar_num] = snapshot.short_exposure

        self.total_margin_interest_cost += snapshot.margin_interest_cost
        self.total_asset_borrow_cost += snapshot.asset_borrow_cost

    def on_position_opened(self, position: Position) -> None:
        self.positions.append(position)
