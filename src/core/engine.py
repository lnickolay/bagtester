from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

from core.broker import Broker
from core.context import Context
from core.data_loader import DataLoader
from core.enums import BarSubstep

if TYPE_CHECKING:
    import pandas as pd

    from core.strategy import Strategy


class Engine:

    _ticker_universe: list[str]
    broker: Broker
    _all_price_data: dict[str, pd.DataFrame]
    # TODO: rename all_trading_days to something that also fits for non-daily bars
    _all_trading_days: np.ndarray

    def __init__(self, ticker_universe: list[str], loader: DataLoader) -> None:
        self._ticker_universe = ticker_universe
        self.broker = Broker(10000.0)
        # TODO: don't load price data of tickers not needed for simulation
        self._all_price_data = loader.load_price_data(ticker_universe)
        self._all_trading_days = self._determine_all_trading_days()

    def run_strategy(
        self,
        strategy: Strategy,
        tickers: list[str] | None = None,
        start_point: np.datetime64 | None = None,
        end_point: np.datetime64 | None = None,
    ) -> pd.Series:
        # TODO: possibly rename runtime measurement variables
        simulation_start_time = time.perf_counter()

        if tickers is None:
            tickers = self._ticker_universe
        if start_point is None:
            start_point = self._all_trading_days[0]
        if end_point is None:
            end_point = self._all_trading_days[-1]

        # TODO: rename trading_days to something that also fits for non-daily bars
        trading_days = self._all_trading_days[
            (self._all_trading_days >= start_point) & (self._all_trading_days <= end_point)
        ]

        print(f"Simulating trading strategy on {len(tickers)} assets for {len(trading_days)} trading days.")

        price_data = {
            ticker: self._all_price_data[ticker].loc[start_point:end_point] for ticker in tickers  # type: ignore[misc]
        }

        indicator_data = strategy.initialize(price_data)

        for bar_step, bar_index in enumerate(trading_days, start=1):
            context = Context(price_data, indicator_data, bar_index, bar_step, BarSubstep.OPEN)
            # TODO: check if this execution order makes sense: the way it is currently implemented, pre_open() uses an
            # outdated broker.equity value
            strategy.pre_open(context)
            self.broker.update(context)

            context = Context(price_data, indicator_data, bar_index, bar_step, BarSubstep.CLOSE)
            strategy.pre_close(context)
            self.broker.update(context)

            if bar_step % 100 == 0:
                print(f"Progress: {bar_step}/{len(trading_days)} trading days simulated.")

        simulation_duration = time.perf_counter() - simulation_start_time
        print(
            f"Finished simulating trading strategy on {len(tickers)} assets for {len(trading_days)} trading "
            + f"days. Total time required to simulate strategy: {simulation_duration:.1f}s"
        )
        print("-" * 10)

        return self.broker.get_equity_series()

    def _determine_all_trading_days(self) -> np.ndarray:
        return np.unique(np.concatenate([df.index.values for df in self._all_price_data.values()]))
