from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import KeysView


class Context:
    price_data: dict[str, pd.DataFrame]
    _indicator_data: dict[str, pd.DataFrame]
    bar_timeline: pd.DatetimeIndex
    bar_time: pd.Timestamp
    bar_num: int

    def __init__(self, price_data: dict[str, pd.DataFrame], indicator_data: dict[str, pd.DataFrame]) -> None:
        self.price_data = price_data
        self._indicator_data = indicator_data
        self.bar_timeline = pd.DatetimeIndex(np.unique(np.concatenate([df.index.values for df in price_data.values()])))
        self.bar_time = pd.NaT  # type: ignore[assignment]
        self.bar_num = -1

    @property
    def bar_count(self) -> int:
        return len(self.bar_timeline)

    def advance_bar(self) -> bool:
        next_bar_num = self.bar_num + 1
        if next_bar_num >= len(self.bar_timeline):
            return False
        else:
            self.bar_num = next_bar_num
            self.bar_time = self.bar_timeline[next_bar_num]
            return True

    def get_price(self, col: str, ticker: str, bars_back: int = 0) -> float:
        df = self.price_data.get(ticker)
        return self._get_value(df, col, bars_back)

    def get_price_ffill(self, col: str, ticker: str, bars_back: int = 0) -> float:
        df = self.price_data.get(ticker)
        return self._get_value(df, col, bars_back, ffill=True)

    def get_indicator(self, col: str, ticker: str, bars_back: int = 0) -> float:
        df = self._indicator_data.get(ticker)
        return self._get_value(df, col, bars_back)

    def get_tickers(self) -> KeysView[str]:
        return self.price_data.keys()

    # def _get_value(self, df: pd.DataFrame | None, col: str, bars_back: int = 0) -> float:
    #     if df is None or col not in df.columns:
    #         return np.nan

    #     if self.bar_time not in df.index:
    #         return np.nan

    #     base_pos = df.index.get_loc(self.bar_time)
    #     assert isinstance(base_pos, int), f"Non-unique index at {self.bar_time}."
    #     pos = base_pos - bars_back

    #     if pos < 0 or pos >= len(df):
    #         return np.nan

    #     return float(df.iloc[pos][col])

    def _get_value(self, df: pd.DataFrame | None, col: str, bars_back: int = 0, ffill: bool = False) -> float:
        if df is None or col not in df.columns:
            return np.nan

        target_pos = self.bar_num - bars_back

        if target_pos < 0 or target_pos >= len(self.bar_timeline):
            if ffill:
                target_pos = max(0, min(target_pos, len(self.bar_timeline) - 1))
            else:
                return np.nan

        target_time = self.bar_timeline[target_pos]

        if target_time in df.index:
            val = float(df.loc[target_time, col])  # type: ignore[arg-type]
        else:
            val = np.nan

        if not np.isnan(val):
            return val
        else:
            if ffill:
                return df[col].asof(target_time)  # type: ignore[return-value]
            else:
                return np.nan
