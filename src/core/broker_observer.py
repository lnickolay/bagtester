from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.events import AccountSnapshot, Execution
    from core.position import Position


class BrokerObserver(ABC):

    def on_account_snapshot(self, snapshot: AccountSnapshot) -> None:
        pass

    def on_order_executed(self, execution: Execution) -> None:
        pass

    def on_position_opened(self, position: Position) -> None:
        pass

    def on_position_closed(self, position: Position) -> None:
        pass
