from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import KeysView

    import pandas as pd


@dataclass
class Context:
    price_data: dict[str, pd.DataFrame]
    _indicator_data: dict[str, pd.DataFrame]
    bar_time: pd.Timestamp
    bar_pos: int
    # bar_substep: BarSubstep
    current_ticker: str = field(default="", init=False)

    def get_price(self, col: str, ticker: str | None = None, bars_back: int = 0) -> float:
        df = self.price_data.get(ticker or self.current_ticker)
        return self._get_value(df, col, bars_back)

    def get_indicator(self, col: str, ticker: str | None = None, bars_back: int = 0) -> float:
        df = self._indicator_data.get(ticker or self.current_ticker)
        return self._get_value(df, col, bars_back)

    def get_tickers(self) -> KeysView[str]:
        return self.price_data.keys()

    def _get_value(self, df: pd.DataFrame | None, col: str, bars_back: int = 0) -> float:
        if df is None or col not in df.columns:
            return np.nan

        if self.bar_time not in df.index:
            return np.nan

        base_pos = df.index.get_loc(self.bar_time)
        assert isinstance(base_pos, int), f"Non-unique index at {self.bar_time}."
        pos = base_pos - bars_back

        if pos < 0 or pos >= len(df):
            return np.nan

        return float(df.iloc[pos][col])
