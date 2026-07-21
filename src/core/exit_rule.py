from __future__ import annotations

from typing import TYPE_CHECKING

from core.condition import LifetimeCondition, PriceCondition
from core.enums import Comparator, ExitRuleType, PositionSide
from core.exit_rule_spec import (
    StopLossFixedSpec,
    StopLossRatioSpec,
    TakeProfitFixedSpec,
    TakeProfitRatioSpec,
    TimedExitSpec,
)
from core.operand import ConstantOperand

if TYPE_CHECKING:
    from core.condition import Condition
    from core.exit_rule_spec import ExitRuleSpec
    from core.position import Position


class ExitRule:

    exit_rule_type: ExitRuleType
    _position: Position
    condition: Condition
    size_pct: float

    def __init__(
        self, exit_rule_type: ExitRuleType, position: Position, condition: Condition, size_pct: float = 1.0
    ) -> None:
        self.exit_rule_type = exit_rule_type
        self._position = position
        self.condition = condition
        self.size_pct = size_pct

    @classmethod
    def from_spec(cls, spec: ExitRuleSpec, position: Position) -> ExitRule:
        cond: Condition

        match spec:
            case StopLossFixedSpec(trigger_price=trigger_price, size_pct=size_pct):
                comp = Comparator.LESS_OR_EQUAL if position.side == PositionSide.LONG else Comparator.GREATER_OR_EQUAL
                cond = PriceCondition(comp, ConstantOperand(trigger_price), evaluated_substeps=spec.evaluated_substeps)
                return cls(ExitRuleType.STOP_LOSS, position, cond, size_pct)

            case StopLossRatioSpec(trigger_ratio=trigger_ratio, size_pct=size_pct):
                comp = Comparator.LESS_OR_EQUAL if position.side == PositionSide.LONG else Comparator.GREATER_OR_EQUAL
                trigger_price = position.entry_price * (1.0 - position.side.sign() * trigger_ratio)
                cond = PriceCondition(comp, ConstantOperand(trigger_price), evaluated_substeps=spec.evaluated_substeps)
                return cls(ExitRuleType.STOP_LOSS, position, cond, size_pct)

            case TakeProfitFixedSpec(trigger_price=trigger_price, size_pct=size_pct):
                comp = Comparator.GREATER_OR_EQUAL if position.side == PositionSide.LONG else Comparator.LESS_OR_EQUAL
                cond = PriceCondition(comp, ConstantOperand(trigger_price), evaluated_substeps=spec.evaluated_substeps)
                return cls(ExitRuleType.TAKE_PROFIT, position, cond, size_pct)

            case TakeProfitRatioSpec(trigger_ratio=trigger_ratio, size_pct=size_pct):
                comp = Comparator.GREATER_OR_EQUAL if position.side == PositionSide.LONG else Comparator.LESS_OR_EQUAL
                trigger_price = position.entry_price * (1.0 + position.side.sign() * trigger_ratio)
                cond = PriceCondition(comp, ConstantOperand(trigger_price), evaluated_substeps=spec.evaluated_substeps)
                return cls(ExitRuleType.TAKE_PROFIT, position, cond, size_pct)

            case TimedExitSpec(lifetime=lifetime, size_pct=size_pct):
                cond = LifetimeCondition(position.entry_bar_pos, lifetime, evaluated_substeps=spec.evaluated_substeps)
                return cls(ExitRuleType.TIMED_EXIT, position, cond, size_pct)

            case _:
                raise ValueError(f"Unsupported comparator: {spec}.")
