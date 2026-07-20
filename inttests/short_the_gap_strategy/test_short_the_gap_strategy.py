import numpy as np
import pytest

from analytics.evaluation import calculate_metrics, plot_pnl_and_drawdowns
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from inttests.helpers import save_test_plot
from strategies.short_the_gap_strategy import ShortTheGapStrategy


def test_short_the_gap_strategy() -> None:
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()

    engine = Engine(tickers, data_loader)
    broker = engine.broker
    strategy = ShortTheGapStrategy(broker, min_gap_up_ratio=0.02)

    start_point = np.datetime64("2015-01-01")
    end_point = np.datetime64("2024-12-31")

    engine.run_strategy(strategy, tickers, start_point, end_point)

    equity_series = broker.get_equity_series()
    eval_metrics = calculate_metrics(equity_series, start_point, end_point)
    fig = plot_pnl_and_drawdowns(equity_series, eval_metrics.drawdown_pct_series)
    save_test_plot(fig, __file__, "pnl_and_drawdowns.png")

    assert broker.opened_positions_counter == 891
    assert broker.closed_positions_counter == 891
    assert eval_metrics.delta_years == pytest.approx(9.99883638952203)
    assert eval_metrics.cagr_pct == pytest.approx(0.627353492894045)
    assert eval_metrics.max_drawdown_pct == pytest.approx(-10.87807936452238)
