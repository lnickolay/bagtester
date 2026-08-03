from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analytics.snapshots import AccountSnapshot


class BrokerObserver(ABC):

    def on_account_snapshot(self, snapshot: AccountSnapshot, bar_num: int) -> None:
        pass
