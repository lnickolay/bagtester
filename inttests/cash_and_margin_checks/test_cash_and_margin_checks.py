import pandas as pd
import pytest

from analytics.evaluation import calculate_metrics, plot_pnl_and_drawdowns
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from inttests.helpers import save_test_plot
from strategies.sma_crossover_strategy import SMACrossoverStrategy


@pytest.mark.skip(reason="Cash and margin checks not implemented yet.")
def test_cash_and_margin_checks() -> None:
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()
    start_time = pd.Timestamp("2024-01-01")
    end_time = pd.Timestamp("2024-12-31")
    price_data = data_loader.load_price_data(tickers, start_time, end_time)

    engine = Engine()
    broker = engine.broker
    strategy = SMACrossoverStrategy(engine.broker, pos_size_ratio=0.5)

    engine.run_strategy(strategy, price_data)

    equity_series = broker.get_equity_series()
    eval_metrics = calculate_metrics(equity_series, start_time, end_time)
    fig = plot_pnl_and_drawdowns(equity_series, eval_metrics.drawdown_pct_series)
    save_test_plot(fig, __file__, "pnl_and_drawdowns.png")

    assert broker.get_equity_series().min() >= 0.0
    assert eval_metrics.max_drawdown_pct >= -100.0
