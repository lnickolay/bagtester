import matplotlib.pyplot as plt
import pandas as pd

from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from evaluation.plotting import plot_and_save_trade_charts, plot_pnl_and_drawdowns
from strategies.sma_crossover_strategy import SMACrossoverStrategy

if __name__ == "__main__":
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()[:5]
    start_time = pd.Timestamp("2024-01-01")
    end_time = pd.Timestamp("2024-12-31")
    price_data = data_loader.load_price_data(tickers, start_time, end_time)

    engine = Engine()
    strategy = SMACrossoverStrategy(engine.broker)

    analysis, history = engine.run_strategy(strategy, price_data)

    plot_and_save_trade_charts(price_data, history)
    fig = plot_pnl_and_drawdowns(analysis.series["equity"], analysis.series["drawdown"])
    plt.show()
