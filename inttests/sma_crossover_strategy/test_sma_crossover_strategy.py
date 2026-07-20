import numpy as np
import pytest

from analytics.evaluation import calculate_metrics, plot_pnl_and_drawdowns
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from inttests.helpers import save_test_plot
from strategies.sma_crossover_strategy import SMACrossoverStrategy


def test_sma_crossover_strategy() -> None:
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()[:5]

    engine = Engine(tickers, data_loader)
    broker = engine.broker
    strategy = SMACrossoverStrategy(engine.broker)

    start_point = np.datetime64("2015-01-01")
    end_point = np.datetime64("2024-12-31")

    engine.run_strategy(strategy, tickers, start_point, end_point)

    equity_series = broker.get_equity_series()
    eval_metrics = calculate_metrics(equity_series, start_point, end_point)
    fig = plot_pnl_and_drawdowns(equity_series, eval_metrics.drawdown_pct_series)
    save_test_plot(fig, __file__, "pnl_and_drawdowns.png")

    assert broker.opened_positions_counter == 271
    assert broker.closed_positions_counter == 0
    assert eval_metrics.delta_years == pytest.approx(9.99883638952203)
    assert eval_metrics.cagr_pct == pytest.approx(73.76051379167852)
    assert eval_metrics.max_drawdown_pct == pytest.approx(-70.88251714377608)
