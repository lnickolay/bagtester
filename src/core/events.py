from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass(frozen=True)
class AccountSnapshot:

    equity: float
    cash: float
    gross_exposure: float
    long_exposure: float
    short_exposure: float
    margin_interest_cost: float
    asset_borrow_cost: float


@dataclass(frozen=True)
class Execution:

    ticker: str
    bar_time: pd.Timestamp
    bar_num: int
    size: float
    base_price: float
    fill_price: float
    maker_fee_cost: float
    taker_fee_cost: float
    liquidation_fee_cost: float
    is_liquidation: bool
