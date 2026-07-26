from enum import Enum, auto


class OrderStatus(Enum):
    ACCEPTED = auto()
    # PARTIALLY_FILLED = auto()
    FILLED = auto()
    # EXPIRED = auto()
    CANCELED = auto()
    REJECTED = auto()


class OrderRole(Enum):
    STOP_LOSS = auto()
    TAKE_PROFIT = auto()


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()
