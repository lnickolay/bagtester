from enum import Enum, auto


class BarSubstep(Enum):
    OPEN = "Open"
    CLOSE = "Close"


class Comparator(Enum):
    LESS = "<"
    GREATER = ">"
    LESS_OR_EQUAL = "<="
    GREATER_OR_EQUAL = ">="


class ExitRuleType(Enum):
    STOP_LOSS = auto()
    TAKE_PROFIT = auto()
    TIMED_EXIT = auto()


class OrderDirection(Enum):
    BUY = 1
    SELL = -1

    def sign(self) -> int:
        return self.value


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()


class PositionSide(Enum):
    LONG = 1
    SHORT = -1

    def sign(self) -> int:
        return self.value
