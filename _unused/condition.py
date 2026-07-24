from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.enums import BarSubstep, Comparator

if TYPE_CHECKING:
    from core.context import Context
    from core.operand import Operand


class Condition(ABC):

    _evaluated_substeps: tuple[BarSubstep, ...]

    def __init__(self, evaluated_substeps: tuple[BarSubstep, ...] = tuple(BarSubstep)) -> None:
        self._evaluated_substeps = evaluated_substeps

    def evaluate(self, context: Context, ticker: str) -> bool:
        if context.bar_substep in self._evaluated_substeps:
            return self._check_condition(context, ticker)
        else:
            return False

    @abstractmethod
    def _check_condition(self, context: Context, ticker: str) -> bool:
        pass


class LifetimeCondition(Condition):

    _from_bar_pos: int
    _lifetime: int

    def __init__(
        self, from_bar_pos: int, lifetime: int, evaluated_substeps: tuple[BarSubstep, ...] = tuple(BarSubstep)
    ) -> None:
        super().__init__(evaluated_substeps)
        self._from_bar_pos = from_bar_pos
        self._lifetime = lifetime

    def _check_condition(self, context: Context, ticker: str) -> bool:
        return context.bar_pos >= self._from_bar_pos + self._lifetime


class PriceCondition(Condition):

    _comparator: Comparator
    _target: Operand

    def __init__(
        self, comparator: Comparator, target: Operand, evaluated_substeps: tuple[BarSubstep, ...] = tuple(BarSubstep)
    ) -> None:
        super().__init__(evaluated_substeps)
        self._comparator = comparator
        self._target = target

    def get_target_value(self, context: Context, ticker: str) -> float:
        return self._target.get_value(context, ticker)

    def _check_condition(self, context: Context, ticker: str) -> bool:
        if context.bar_substep == BarSubstep.OPEN:
            price = context.get_price(ticker, "Open")
        else:
            if self._comparator in (Comparator.LESS, Comparator.LESS_OR_EQUAL):
                price = context.get_price(ticker, "Low")
            else:
                price = context.get_price(ticker, "High")

        target_value = self.get_target_value(context, ticker)

        match self._comparator:
            case Comparator.LESS:
                return price < target_value
            case Comparator.LESS_OR_EQUAL:
                return price <= target_value
            case Comparator.GREATER:
                return price > target_value
            case Comparator.GREATER_OR_EQUAL:
                return price >= target_value
            case _:
                raise ValueError(f"Unsupported comparator: {self.comparator}.")
