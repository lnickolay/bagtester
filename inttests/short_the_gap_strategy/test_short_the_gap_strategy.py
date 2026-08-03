import pandas as pd
import pytest

from analytics.evaluation import calculate_metrics, plot_pnl_and_drawdowns
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from inttests.helpers import save_test_plot
from strategies.short_the_gap_strategy import ShortTheGapStrategy


def test_short_the_gap_strategy() -> None:
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()
    start_time = pd.Timestamp("2015-01-01")
    end_time = pd.Timestamp("2024-12-31")
    price_data = data_loader.load_price_data(tickers, start_time, end_time)

    engine = Engine()
    broker = engine.broker
    strategy = ShortTheGapStrategy(broker)

    history = engine.run_strategy(strategy, price_data)

    equity_series = history.account_history["equity"]
    eval_metrics = calculate_metrics(equity_series, start_time, end_time)
    fig = plot_pnl_and_drawdowns(equity_series, eval_metrics.drawdown_pct_series)
    save_test_plot(fig, __file__, "pnl_and_drawdowns.png")

    assert broker.opened_positions_counter == 33
    assert broker.closed_positions_counter == 33
    assert eval_metrics.delta_years == pytest.approx(9.99883638952203)
    assert eval_metrics.cagr_pct == pytest.approx(0.151887501940684)
    assert eval_metrics.max_drawdown_pct == pytest.approx(-4.698777618061622)
