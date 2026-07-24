from dataclasses import dataclass, field

from core.enums import BarSubstep


@dataclass
class ExitRuleSpec:
    size_pct: float = field(default=1.0, kw_only=True)
    evaluated_substeps: tuple[BarSubstep, ...] = field(default_factory=lambda: tuple(BarSubstep), kw_only=True)


@dataclass
class StopLossFixedSpec(ExitRuleSpec):
    trigger_price: float


@dataclass
class StopLossRatioSpec(ExitRuleSpec):
    trigger_ratio: float


@dataclass
class TakeProfitFixedSpec(ExitRuleSpec):
    trigger_price: float


@dataclass
class TakeProfitRatioSpec(ExitRuleSpec):
    trigger_ratio: float


@dataclass
class TimedExitSpec(ExitRuleSpec):
    lifetime: int
