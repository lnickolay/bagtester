from enum import Enum, auto


class OrderStatus(Enum):
    SUBMITTED = auto()
    ACCEPTED = auto()
    FILLED = auto()
    EXPIRED = auto()
    CANCELED = auto()
    REJECTED = auto()


class OrderRole(Enum):
    STANDARD = 0
    TAKE_PROFIT = 1
    STOP_LOSS = 2


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
