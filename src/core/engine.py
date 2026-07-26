from __future__ import annotations

import time
from typing import TYPE_CHECKING

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
        indicator_data = strategy.initialize(price_data)

        context = Context(price_data, indicator_data)
        print(f"Simulating trading strategy on {len(price_data)} assets for {len(context.bar_timeline)} trading days.")

        while context.advance_bar():
            self.broker.update(context)
            strategy.process(context)

            if (context.bar_num + 1) % 100 == 0:
                print(f"Progress: {context.bar_num + 1}/{len(context.bar_timeline)} trading days simulated.")

        simulation_timer_elapsed = time.perf_counter() - simulation_timer_start
        print(
            f"Finished simulating trading strategy on {len(price_data)} assets for {len(context.bar_timeline)} trading "
            + f"days. Total time required to simulate strategy: {simulation_timer_elapsed:.1f}s"
        )
        print("-" * 10)

        return self.broker.get_equity_series()
