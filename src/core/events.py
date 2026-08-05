from dataclasses import dataclass


@dataclass(frozen=True)
class AccountSnapshot:

    equity: float
    cash: float
    gross_exposure: float
    long_exposure: float
    short_exposure: float
    margin_interest_cost: float
    asset_borrow_cost: float
