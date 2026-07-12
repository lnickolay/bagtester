import numpy as np

from analytics.evaluation import show_results
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from strategies.short_the_gap_strategy import ShortTheGapStrategy

if __name__ == "__main__":
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()

    engine = Engine(tickers, data_loader)
    strategy = ShortTheGapStrategy(engine.broker, min_gap_up_pct=0.02)

    start_point = np.datetime64("2015-01-01")
    end_point = np.datetime64("2024-12-31")

    engine.run_strategy(strategy, tickers, start_point, end_point)
    show_results(engine.broker, start_point, end_point)
