from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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

    account_snapshots: list[AccountSnapshot]
    executions: dict[str, list[Execution]]
    trades: dict[str, list[Trade]]
    open_trades: dict[str, Trade]

    _open_trade_pointers: dict[str, int]

    def __init__(self) -> None:
        self.account_snapshots = []
        self.executions = {}
        self.trades = {}
        self.open_trades = {}

        self._open_trade_pointers = {}

    def finalize_open_trades(self) -> None:
        for ticker, start in self._open_trade_pointers.items():
            self.open_trades[ticker] = Trade(ticker, tuple(self.executions[ticker][start:]), False)
            self.trades.setdefault(ticker, []).append(self.open_trades[ticker])
        self._open_trade_pointers.clear()

    def on_account_snapshot(self, snapshot: AccountSnapshot) -> None:
        self.account_snapshots.append(snapshot)

    def on_order_executed(self, execution: Execution) -> None:
        self.executions.setdefault(execution.ticker, []).append(execution)

    def on_position_opened(self, position: Position) -> None:
        self._open_trade_pointers[position.ticker] = len(self.executions[position.ticker]) - 1

    def on_position_closed(self, position: Position) -> None:
        ticker = position.ticker
        start = self._open_trade_pointers.pop(ticker)
        self.trades.setdefault(ticker, []).append(Trade(ticker, tuple(self.executions[ticker][start:])))
