from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import Context


class Operand(ABC):

    @abstractmethod
    def get_value(self, context: Context, ticker: str) -> float:
        pass


class ConstantOperand(Operand):

    value: float

    def __init__(self, value: float) -> None:
        self.value = value

    def get_value(self, context: Context, ticker: str) -> float:
        return self.value


class IndicatorOperand(Operand):

    col: str

    def __init__(self, col: str) -> None:
        self.col = col

    def get_value(self, context: Context, ticker: str) -> float:
        return context.get_indicator(ticker, self.col)
