from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from core.broker_observer import BrokerObserver

if TYPE_CHECKING:
    import pandas as pd

    from core.events import AccountSnapshot, Execution
    from core.position import Position


@dataclass(frozen=True)
class Trade:

    ticker: str
    executions: tuple[Execution, ...]
    closed: bool = True

    @property
    def entry_bar_time(self) -> pd.Timestamp:
        return self.executions[0].bar_time

    @property
    def entry_bar_num(self) -> int:
        return self.executions[0].bar_num

    @property
    def exit_bar_time(self) -> pd.Timestamp | None:
        return self.executions[-1].bar_time if self.closed else None

    @property
    def exit_bar_num(self) -> int | None:
        return self.executions[-1].bar_num if self.closed else None


class History(BrokerObserver):

    equity_series: np.ndarray
    cash_series: np.ndarray
    gross_exposure_series: np.ndarray
    long_exposure_series: np.ndarray
    short_exposure_series: np.ndarray

    total_maker_fee_cost: float
    total_taker_fee_cost: float
    total_liquidation_fee_cost: float
    total_slippage_cost: float
    total_margin_interest_cost: float
    total_asset_borrow_cost: float

    executions: dict[str, list[Execution]]
    trades: dict[str, list[Trade]]
    open_trades: dict[str, Trade]

    _open_trade_pointers: dict[str, int]

    def __init__(self, bar_count: int) -> None:
        self.equity_series = np.empty(bar_count)
        self.cash_series = np.empty(bar_count)
        self.gross_exposure_series = np.empty(bar_count)
        self.long_exposure_series = np.empty(bar_count)
        self.short_exposure_series = np.empty(bar_count)

        self.total_maker_fee_cost = 0.0
        self.total_taker_fee_cost = 0.0
        self.total_liquidation_fee_cost = 0.0
        self.total_slippage_cost = 0.0
        self.total_margin_interest_cost = 0.0
        self.total_asset_borrow_cost = 0.0

        self.executions = {}
        self._open_trade_pointers = {}
        self.trades = {}
        self.open_trades = {}

    def finalize(self) -> None:
        for ticker, start in self._open_trade_pointers.items():
            self.open_trades[ticker] = Trade(ticker, tuple(self.executions[ticker][start:]), False)
            self.trades.setdefault(ticker, []).append(self.open_trades[ticker])
        self._open_trade_pointers.clear()

    def on_account_snapshot(self, snapshot: AccountSnapshot, bar_num: int) -> None:
        self.equity_series[bar_num] = snapshot.equity
        self.cash_series[bar_num] = snapshot.cash
        self.gross_exposure_series[bar_num] = snapshot.gross_exposure
        self.long_exposure_series[bar_num] = snapshot.long_exposure
        self.short_exposure_series[bar_num] = snapshot.short_exposure

        self.total_margin_interest_cost += snapshot.margin_interest_cost
        self.total_asset_borrow_cost += snapshot.asset_borrow_cost

    def on_order_executed(self, execution: Execution) -> None:
        self.executions.setdefault(execution.ticker, []).append(execution)
        self.total_maker_fee_cost += execution.maker_fee_cost
        self.total_taker_fee_cost += execution.taker_fee_cost
        self.total_liquidation_fee_cost += execution.liquidation_fee_cost
        self.total_slippage_cost += execution.size * (execution.fill_price - execution.base_price)

    def on_position_opened(self, position: Position) -> None:
        self._open_trade_pointers[position.ticker] = len(self.executions[position.ticker]) - 1

    def on_position_closed(self, position: Position) -> None:
        ticker = position.ticker
        start = self._open_trade_pointers.pop(ticker)
        self.trades.setdefault(ticker, []).append(Trade(ticker, tuple(self.executions[ticker][start:])))
