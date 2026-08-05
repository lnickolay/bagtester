from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pandas as pd

from core.broker import Broker
from core.context import Context
from evaluation.analysis import Analysis
from evaluation.history import History

if TYPE_CHECKING:
    from core.strategy import Strategy


class Engine:

    broker: Broker

    def __init__(self, broker: Broker | None = None) -> None:
        self.broker = broker or Broker()

    def run_strategy(self, strategy: Strategy, price_data: dict[str, pd.DataFrame]) -> Analysis:
        simulation_timer_start = time.perf_counter()
        indicator_data = strategy.initialize(price_data)

        context = Context(price_data, indicator_data)
        history = History(len(context.bar_timeline))
        self.broker.add_observer(history)

        print(f"Simulating trading strategy on {len(price_data)} assets for {context.bar_count} trading days.")

        while context.advance_bar():
            self.broker.update(context)
            strategy.process(context)

            if (context.bar_num + 1) % 100 == 0:
                print(f"Progress: {context.bar_num + 1}/{context.bar_count} trading days simulated.")

        simulation_timer_elapsed = time.perf_counter() - simulation_timer_start
        print(
            f"Finished simulating trading strategy on {len(price_data)} assets for {context.bar_count} trading "
            + f"days. Total time required to simulate strategy: {simulation_timer_elapsed:.1f}s"
        )
        print("-" * 10)

        self.broker.remove_observer(history)
        analysis = Analysis(history, context.bar_timeline, self.broker.initial_cash)

        return analysis
