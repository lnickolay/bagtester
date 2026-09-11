from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class Position:

    ticker: str
    size: float
    avg_price: float
    entry_bar_time: pd.Timestamp
    entry_bar_num: int
    exit_bar_time: pd.Timestamp | None = None
    exit_bar_num: int | None = None
