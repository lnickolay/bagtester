import numpy as np

from analytics.evaluation import calculate_metrics, plot_pnl_and_drawdowns
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from inttests.helpers import save_test_plot
from strategies.sma_crossover_strategy import SMACrossoverStrategy


def test_cash_and_margin_checks() -> None:
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()

    engine = Engine(tickers, data_loader)
    broker = engine.broker
    strategy = SMACrossoverStrategy(engine.broker, pos_size_ratio=0.5)

    start_point = np.datetime64("2024-01-01")
    end_point = np.datetime64("2024-12-31")

    engine.run_strategy(strategy, tickers, start_point, end_point)

    equity_series = broker.get_equity_series()
    eval_metrics = calculate_metrics(equity_series, start_point, end_point)
    fig = plot_pnl_and_drawdowns(equity_series, eval_metrics.drawdown_pct_series)
    save_test_plot(fig, __file__, "pnl_and_drawdowns.png")

    assert broker.get_equity_series().min() >= 0.0
    assert eval_metrics.max_drawdown_pct >= -100.0
