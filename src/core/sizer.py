from abc import ABC, abstractmethod


class Sizer(ABC):

    @abstractmethod
    def calc_order_size(self, price: float, equity: float, stop_loss_price: float | None) -> float:
        pass


class FixedValueSizer(Sizer):

    _fixed_value: float

    def __init__(self, fixed_value: float) -> None:
        self._fixed_value = fixed_value

    def calc_order_size(self, price: float, equity: float, stop_loss_price: float | None) -> float:
        return self._fixed_value / price


class EquityRatioSizer(Sizer):

    _equity_ratio: float

    def __init__(self, equity_ratio: float) -> None:
        self._equity_ratio = equity_ratio

    def calc_order_size(self, price: float, equity: float, stop_loss_price: float | None) -> float:
        return self._equity_ratio * equity / price


class FixedRiskSizer(Sizer):

    _fixed_risk: float

    def __init__(self, fixed_risk: float) -> None:
        self._fixed_risk = fixed_risk

    def calc_order_size(self, price: float, equity: float, stop_loss_price: float | None) -> float:
        if stop_loss_price is None:
            raise ValueError("FixedRiskSizer requires a stop loss price.")

        return self._fixed_risk * equity / abs(price - stop_loss_price)
