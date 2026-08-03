from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from analytics.history import History
    from core.broker import Broker


@dataclass(frozen=True)
class EvalMetrics:
    delta_years: float
    cagr_pct: float
    max_drawdown_pct: float
    drawdown_pct_series: pd.Series


# TODO: show_results() probably shouldn't need to know broker
def show_results(broker: Broker, history: History, start_time: pd.Timestamp, end_time: pd.Timestamp) -> Figure:
    equity_series = history.account_history["equity"]
    eval_metrics = calculate_metrics(equity_series, start_time, end_time)

    print(f"Simulated timespan: {eval_metrics.delta_years:.2f} years")
    print(f"Opened / closed positions: {broker.opened_positions_counter} / {broker.closed_positions_counter}")
    print(f"CAGR: {eval_metrics.cagr_pct:.2f}%")
    print(f"Max Drawdown: {eval_metrics.max_drawdown_pct:.2f}%")
    print("Plotting PnL and drawdown graphs.")

    return plot_pnl_and_drawdowns(equity_series, eval_metrics.drawdown_pct_series)


def calculate_metrics(equity_series: pd.Series, start_time: pd.Timestamp, end_time: pd.Timestamp) -> EvalMetrics:
    # calculate drawdowns
    running_max_series = equity_series.cummax()
    drawdown_pct_series = ((equity_series - running_max_series) / running_max_series) * 100.0

    start_balance = equity_series.iloc[0]
    end_balance = equity_series.iloc[-1]

    delta_years = pd.Timedelta(end_time - start_time).days / 365.2425
    cagr_pct = (((end_balance / start_balance) ** (1 / delta_years)) - 1.0) * 100.0

    return EvalMetrics(
        delta_years=delta_years,
        cagr_pct=cagr_pct,
        max_drawdown_pct=drawdown_pct_series.min(),
        drawdown_pct_series=drawdown_pct_series,
    )


def plot_pnl_and_drawdowns(equity_series: pd.Series, drawdown_pct_series: pd.Series) -> Figure:
    fig, (ax_eq, ax_dd) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

    # configure PnL curve
    ax_eq.plot(equity_series, linewidth=1.5, color="blue")
    ax_eq.set_ylabel("Account Balance")
    ax_eq.set_yscale("log")
    # suppress scientific notation for Y axis labels
    ax_eq.yaxis.set_major_formatter(mtick.ScalarFormatter())
    ax_eq.yaxis.set_minor_formatter(mtick.ScalarFormatter())
    ax_eq.yaxis.get_major_formatter().set_scientific(False)
    ax_eq.yaxis.get_minor_formatter().set_scientific(False)
    ax_eq.set_title("PnL Curve")
    ax_eq.grid(True, linestyle="--", alpha=0.3)

    # configure drawdown curve
    ax_dd.plot(drawdown_pct_series, color="red", linewidth=1)
    ax_dd.fill_between(drawdown_pct_series.index, drawdown_pct_series, 0, color="red", alpha=0.3)
    ax_dd.set_ylabel("Drawdown %")
    ax_dd.set_ylim(min(drawdown_pct_series.min(), -25.0), 0.0)
    ax_dd.set_title("Drawdowns")
    ax_dd.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    return fig
