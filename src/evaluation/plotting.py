from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import mplfinance as mpf
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from paths import OUTPUT_DIR

if TYPE_CHECKING:
    from evaluation.history import History, Trade


_TRADE_BARS_PADDING = 20
_MARKER_Y_OFFSET = 0.05
_MARKER_SIZE = 80
_MPF_CHARLES_GREEN = "#006340"
_MPF_CHARLES_RED = "#a02128"


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


def plot_and_save_trade_charts(
    price_data: dict[str, pd.DataFrame], history: History, output_dir: Path | str | None = None
) -> None:
    if output_dir is not None:
        output_dir = Path(output_dir)
    else:
        output_dir = OUTPUT_DIR / "trade_charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    for ticker, ticker_trades in history.trades.items():
        for i, trade in enumerate(ticker_trades):
            fig = _plot_trade_chart(price_data, trade, i + 1)
            fig.savefig(output_dir / f"{ticker}_trade_{i + 1}.png")
            plt.close(fig)


def _plot_trade_chart(price_data: dict[str, pd.DataFrame], trade: Trade, trade_num: int) -> Figure:
    ticker_df = price_data[trade.ticker]
    entry_bar_num = cast(int, ticker_df.index.get_loc(trade.entry_bar_time))
    window_start_bar_num = max(entry_bar_num - _TRADE_BARS_PADDING, 0)
    if trade.closed:
        exit_bar_num = cast(int, ticker_df.index.get_loc(trade.exit_bar_time))
        window_end_bar_num = min(exit_bar_num + _TRADE_BARS_PADDING, len(ticker_df) - 1)
    else:
        window_end_bar_num = len(ticker_df) - 1
    df_window = ticker_df.iloc[window_start_bar_num : window_end_bar_num + 1]

    buy_markers = pd.Series(np.nan, index=df_window.index)
    sell_markers = pd.Series(np.nan, index=df_window.index)
    spread = df_window["High"].max() - df_window["Low"].min()
    for execution in trade.executions:
        if execution.size > 0.0:
            buy_markers.at[execution.bar_time] = df_window.at[execution.bar_time, "Low"] - _MARKER_Y_OFFSET * spread
        else:
            sell_markers.at[execution.bar_time] = df_window.at[execution.bar_time, "High"] + _MARKER_Y_OFFSET * spread

    addplots = []
    if np.isfinite(buy_markers).any():
        addplots.append(
            mpf.make_addplot(buy_markers, type="scatter", markersize=_MARKER_SIZE, marker="^", color=_MPF_CHARLES_GREEN)
        )
    if np.isfinite(sell_markers).any():
        addplots.append(
            mpf.make_addplot(sell_markers, type="scatter", markersize=_MARKER_SIZE, marker="v", color=_MPF_CHARLES_RED)
        )

    fig, axlist = mpf.plot(
        df_window,
        type="candle",
        style="charles",
        addplot=addplots,
        figsize=(12, 8),
        returnfig=True,
        scale_padding={"left": 0.2, "right": 0.7, "top": 0.5, "bottom": 0.5},
    )
    axlist[0].set_title(f"{trade.ticker} trade #{trade_num}")
    return cast(Figure, fig)
