from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from core.condition import PriceCondition
from core.enums import BarSubstep, OrderType
from core.order import Order
from core.position import Position
from debug_settings import PRINT_DEBUG_OUTPUT

if TYPE_CHECKING:
    from core.context import Context
    from core.exit_rule import ExitRule


class Broker:

    _cash: float
    equity: float
    _initial_equity: float
    _equity_history: list[tuple[pd.Timestamp, float]]
    _orders: dict[str, Order]
    _positions: dict[str, Position]
    # TODO: track opened and closed positions etc differently
    opened_positions_counter: int
    closed_positions_counter: int

    def __init__(self, cash: float) -> None:
        self._cash = cash
        self.equity = cash
        self._initial_equity = cash
        self._equity_history = []
        # TODO: use a different data structure instead of dicts to support multiple orders per ticker
        self._orders = {}
        self._positions = {}
        self.opened_positions_counter = 0
        self.closed_positions_counter = 0

    def submit_order(self, order: Order) -> None:
        self._orders[order.ticker] = order

    def get_equity_series(self) -> pd.Series:
        bar_indexes, equities = zip(*self._equity_history)
        return pd.Series(equities, index=bar_indexes)

    def get_position(self, ticker: str) -> Position | None:
        return self._positions.get(ticker)

    def update(self, context: Context) -> None:
        self._update_orders(context)
        self._update_positions(context)
        self._update_equity(context)

    def _update_orders(self, context: Context) -> None:
        executed_orders = []

        for ticker, order in self._orders.items():
            if order.order_type == OrderType.MARKET:
                # TODO: check if ticker gets traded on current bar and only open a position if that is the case
                self._open_position(order, context)
                executed_orders.append(order)
            elif order.order_type == OrderType.LIMIT:
                # TODO: implement market orders
                pass

        for order in executed_orders:
            del self._orders[order.ticker]

    def _update_positions(self, context: Context) -> None:
        closed_positions = []

        for ticker, position in self._positions.items():
            ordered_exit_rules = position.stop_loss_rules + position.take_profit_rules + position.timed_exit_rules

            for exit_rule in ordered_exit_rules:
                if exit_rule.condition.evaluate(context, ticker):

                    self._close_partial_position(position, exit_rule, context)
                    if position.size <= 0:
                        closed_positions.append(position)
                        self.closed_positions_counter += 1
                        break

        for position in closed_positions:
            del self._positions[position.ticker]

    def _update_equity(self, context: Context) -> None:
        # TODO: replace direct access to context.price_data with a method (e.g. get_price_asof()) so price_data can be
        # made internal
        most_recent_prices = {
            ticker: pd.Series(
                {
                    # asof() gets the last non-NaN price
                    col: context.price_data[ticker][col].asof(context.bar_index)
                    for col in context.price_data[ticker].columns
                }
            )
            for ticker in self._get_open_tickers()
        }

        equity = self._cash
        for ticker, position in self._positions.items():
            equity += position.side.sign() * position.size * most_recent_prices[ticker][context.bar_substep.value]
        self.equity = equity

        if context.bar_substep == BarSubstep.CLOSE:
            if not self._equity_history:
                self._equity_history.append((context.bar_index, self._initial_equity))
            self._equity_history.append((context.bar_index, equity))

    def _get_open_tickers(self) -> set[str]:
        return set(self._orders.keys()) | set(self._positions.keys())

    # TODO: check cash sufficiency before opening a position (currently positions can exceed available cash)
    # def can_open(self, order: Order, price: float) -> bool:
    #     return self._cash >= order.size * price

    # TODO: implement position scaling by making it possible to execute multiple orders on the same ticker
    def _open_position(self, order: Order, context: Context) -> Position:
        price = context.get_price(order.ticker, context.bar_substep.value)
        total_value = order.size * price
        self._cash -= order.direction.sign() * total_value
        position = Position.from_order(order, price, context.bar_index, context.bar_step)
        self._positions[order.ticker] = position
        self.opened_positions_counter += 1

        if PRINT_DEBUG_OUTPUT:
            print(
                f"{pd.Timestamp(context.bar_index).date()} - Opened new {position.side.name} position. "
                + f"Ticker: {position.ticker}, Price {price:.2f}, Size: {order.size:.2f}, "
                + f"Total value: {total_value:.2f}."
            )

        return position

    def _close_partial_position(self, position: Position, exit_rule: ExitRule, context: Context) -> None:
        if context.bar_substep == BarSubstep.OPEN:
            price = context.get_price(position.ticker, "Open")
        else:
            # context.bar_substep == BarSubstep.CLOSE
            if isinstance(exit_rule.condition, PriceCondition):
                price = exit_rule.condition.get_target_value(context, position.ticker)
            else:
                price = context.get_price(position.ticker, "Close")

        if exit_rule.size_pct < position.size_pct:
            size_pct_to_close = exit_rule.size_pct
            size_to_close = exit_rule.size_pct * position.initial_size
            position.size -= size_to_close
            position.size_pct -= size_pct_to_close
        else:
            size_pct_to_close = position.size_pct
            size_to_close = position.size
            position.size = 0.0
            position.size_pct = 0.0

        self._cash += position.side.sign() * size_to_close * price

        if PRINT_DEBUG_OUTPUT:
            print(
                f"{pd.Timestamp(context.bar_index).date()} ({context.bar_substep.name}) - "
                + f"Closed {position.side.name} position. Reason: {exit_rule.exit_rule_type.name}, "
                + f"Ticker: {position.ticker}, Price {price:.2f}, Size: {size_to_close:.2f}, "
                + f"Total value: {size_to_close * price:.2f}."
            )
