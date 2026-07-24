from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from core.broker import Broker
from core.context import Context

if TYPE_CHECKING:
    from core.strategy import Strategy


class Engine:

    broker: Broker

    def __init__(self, initial_cash: float = 10000.0) -> None:
        self.broker = Broker(initial_cash)

    def run_strategy(self, strategy: Strategy, price_data: dict[str, pd.DataFrame]) -> pd.Series:
        simulation_timer_start = time.perf_counter()
        bar_times = pd.DatetimeIndex(np.unique(np.concatenate([df.index.values for df in price_data.values()])))
        print(f"Simulating trading strategy on {len(price_data)} assets for {len(bar_times)} trading days.")

        indicator_data = strategy.initialize(price_data)

        # for bar_pos, bar_time in enumerate(bar_times, start=1):
        #     context = Context(price_data, indicator_data, bar_time, bar_pos, BarSubstep.OPEN)
        #     strategy.pre_open(context)
        #     self.broker.update(context)
        #
        #     context = Context(price_data, indicator_data, bar_time, bar_pos, BarSubstep.CLOSE)
        #     strategy.pre_close(context)
        #     self.broker.update(context)
        #
        #     if bar_pos % 100 == 0:
        #         print(f"Progress: {bar_pos}/{len(bar_times)} trading days simulated.")

        context = Context(price_data, indicator_data, bar_times[0], 0)

        for bar_pos, bar_time in enumerate(bar_times, start=1):
            context.bar_time = bar_time
            context.bar_pos = bar_pos

            self.broker.update(context)

            for ticker in price_data:
                context.current_ticker = ticker
                strategy.process_ticker(context)

            if bar_pos % 100 == 0:
                print(f"Progress: {bar_pos}/{len(bar_times)} trading days simulated.")

        simulation_timer_elapsed = time.perf_counter() - simulation_timer_start
        print(
            f"Finished simulating trading strategy on {len(price_data)} assets for {len(bar_times)} trading "
            + f"days. Total time required to simulate strategy: {simulation_timer_elapsed:.1f}s"
        )
        print("-" * 10)

        return self.broker.get_equity_series()
