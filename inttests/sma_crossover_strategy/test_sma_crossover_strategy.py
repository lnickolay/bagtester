import pandas as pd
import pytest

from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from evaluation.plotting import plot_pnl_and_drawdowns
from inttests.helpers import save_test_plot
from strategies.sma_crossover_strategy import SMACrossoverStrategy


def test_sma_crossover_strategy() -> None:
    data_loader = YFinanceDataLoader("sample")
    tickers = data_loader.get_included_tickers()[:5]
    start_time = pd.Timestamp("2015-01-01")
    end_time = pd.Timestamp("2024-12-31")
    price_data = data_loader.load_price_data(tickers, start_time, end_time)

    engine = Engine()
    strategy = SMACrossoverStrategy(engine.broker)

    analysis, _ = engine.run_strategy(strategy, price_data)

    fig = plot_pnl_and_drawdowns(analysis.series["equity"], analysis.series["drawdown"])
    save_test_plot(fig, __file__, "pnl_and_drawdowns.png")

    assert analysis.opened_position_count == 271
    assert analysis.closed_position_count == 266
    assert analysis.duration_years == pytest.approx(9.993360575508055)
    assert analysis.cagr == pytest.approx(0.007217326953825376)
    assert analysis.max_drawdown == pytest.approx(-0.2947383265762063)
