import matplotlib.pyplot as plt
import pandas as pd

from analytics.evaluation import show_results
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from strategies.sma_crossover_strategy import SMACrossoverStrategy

if __name__ == "__main__":
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()[:5]
    start_time = pd.Timestamp("2015-01-01")
    end_time = pd.Timestamp("2024-12-31")
    price_data = data_loader.load_price_data(tickers, start_time, end_time)

    engine = Engine()
    strategy = SMACrossoverStrategy(engine.broker)

    engine.run_strategy(strategy, price_data)
    fig = show_results(engine.broker, start_time, end_time)
    plt.show()
