from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.figure import Figure


def plot_pnl_and_drawdowns(equity_series: pd.Series, drawdown_series: pd.Series) -> Figure:
    fig, (ax_eq, ax_dd) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

    # configure PnL curve
    ax_eq.plot(equity_series, linewidth=1.5, color="blue")
    ax_eq.set_ylabel("Account Balance")
    # ax_eq.set_yscale("log")
    ax_eq.set_xlim(equity_series.index[0], equity_series.index[-1])
    # suppress scientific notation for Y axis labels
    ax_eq.yaxis.set_major_formatter(mtick.ScalarFormatter())
    ax_eq.yaxis.set_minor_formatter(mtick.ScalarFormatter())
    ax_eq.yaxis.get_major_formatter().set_scientific(False)
    ax_eq.yaxis.get_minor_formatter().set_scientific(False)
    ax_eq.set_title("PnL Curve")
    ax_eq.grid(True, linestyle="--", alpha=0.3)

    # configure drawdown curve
    ax_dd.plot(drawdown_series, color="red", linewidth=1)
    ax_dd.fill_between(drawdown_series.index, drawdown_series, 0, color="red", alpha=0.3)
    ax_dd.set_ylabel("Drawdown %")
    # ax_dd.set_ylim(min(drawdown_pct_series.min(), -0.25), 0.0)
    ax_dd.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
    ax_dd.set_title("Drawdowns")
    ax_dd.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    return fig
