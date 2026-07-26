from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING

import pandas as pd

from core.enums import OrderType
from core.order import Order
from core.position import Position

if TYPE_CHECKING:
    from core.context import Context


# TODO: properly handle case where price is NaN for ticker on current bar during order execution, equity calculation etc
class Broker:

    _cash: float
    equity: float
    _initial_equity: float
    _equity_history: list[tuple[pd.Timestamp, float]]
    _gross_exposure: float
    _immediate_orders: list[Order]
    _conditional_orders: list[Order]
    _positions: dict[str, Position]
    _initial_margin: float
    _maintenance_margin: float
    _liquidation_fee: float
    # TODO: track opened and closed positions etc differently
    opened_positions_counter: int
    closed_positions_counter: int

    def __init__(
        self,
        cash: float,
        initial_margin: float = 1.0,
        maintenance_margin: float = 0.0,
        liquidation_fee: float = 0.0,
    ) -> None:
        self._cash = cash
        self.equity = cash
        self._initial_equity = cash
        self._equity_history = []
        self._gross_exposure = 0.0
        self._immediate_orders = []
        self._conditional_orders = []
        self._positions = {}
        self._initial_margin = initial_margin
        self._maintenance_margin = maintenance_margin
        self._liquidation_fee = liquidation_fee
        self.opened_positions_counter = 0
        self.closed_positions_counter = 0

    def submit_order(self, order: Order) -> None:
        self._immediate_orders.append(order)

    def get_equity_series(self) -> pd.Series:
        bar_timeline, equities = zip(*self._equity_history)
        return pd.Series(equities, index=bar_timeline)

    def get_position(self, ticker: str) -> Position | None:
        return self._positions.get(ticker)

    def update(self, context: Context) -> None:
        self._update_equity_and_gross_exposure(context, "Open")
        self._handle_immediate_orders(context)
        self._handle_conditional_orders(context)
        self._update_equity_and_gross_exposure(context, "Close")
        if self._is_below_maintenance():
            self._liquidate(context)
            self._update_equity_and_gross_exposure(context, "Close")

    def _handle_immediate_orders(self, context: Context) -> None:
        remaining = list(self._immediate_orders)
        self._immediate_orders.clear()
        for order in remaining:
            price = context.get_price("Open", order.ticker)
            if math.isnan(price) or not self._can_open(order, price, context):
                continue
            self._fill(order, price, context)

    def _handle_conditional_orders(self, context: Context) -> None:
        pass

    def _calc_gross_delta(self, order: Order, price: float) -> float:
        existing_position = self._positions.get(order.ticker)
        existing_size = existing_position.size if existing_position is not None else 0.0
        return price * (abs(existing_size + order.size) - abs(existing_size))

    def _can_open(self, order: Order, price: float, context: Context) -> bool:
        new_gross = self._gross_exposure + self._calc_gross_delta(order, price)
        if new_gross > 0 and self.equity / new_gross < self._initial_margin:
            warnings.warn("Order would breach initial margin, skipping.")
            return False
        return True

    def _fill(self, order: Order, price: float, context: Context) -> None:
        self._gross_exposure += self._calc_gross_delta(order, price)
        self._cash -= order.size * price

        existing_position = self._positions.get(order.ticker)

        if existing_position is None:
            self._positions[order.ticker] = Position.from_order(order, price, context.bar_time, context.bar_num)
            self.opened_positions_counter += 1
            return

        new_size = existing_position.size + order.size

        if new_size == 0:
            del self._positions[order.ticker]
            self.closed_positions_counter += 1
        elif (existing_position.size > 0) == (new_size > 0):
            existing_position.size = new_size
        else:
            del self._positions[order.ticker]
            self.closed_positions_counter += 1
            if new_size != 0:
                flip_position = Position(
                    ticker=order.ticker,
                    size=new_size,
                    entry_price=price,
                    entry_bar_time=context.bar_time,
                    entry_bar_num=context.bar_num,
                )
                self._positions[order.ticker] = flip_position
                self.opened_positions_counter += 1

    # def _update_equity(self, context: Context) -> None:
    #     # TODO: replace direct access to context.price_data with a method (e.g. get_price_asof()) so price_data can be
    #     # made internal
    #     most_recent_prices = {
    #         ticker: pd.Series(
    #             {
    #                 # asof() gets the last non-NaN price
    #                 col: context.price_data[ticker][col].asof(context.bar_time)
    #                 for col in context.price_data[ticker].columns
    #             }
    #         )
    #         for ticker in self._positions
    #     }
    #
    #     equity = self._cash
    #     for ticker, position in self._positions.items():
    #         equity += position.size * most_recent_prices[ticker]["Close"]
    #     self.equity = equity
    #
    #     if not self._equity_history:
    #         self._equity_history.append((context.bar_time, self._initial_equity))
    #     self._equity_history.append((context.bar_time, equity))

    def _update_equity_and_gross_exposure(self, context: Context, price_col: str) -> None:
        equity = self._cash
        gross_exposure = 0.0
        for ticker, position in self._positions.items():
            price = context.get_price_ffill(price_col, ticker)
            value = position.size * price
            equity += value
            gross_exposure += abs(value)
        self.equity = equity
        self._gross_exposure = gross_exposure

        if price_col == "Close":
            if not self._equity_history:
                self._equity_history.append((context.bar_time, self._initial_equity))
            self._equity_history.append((context.bar_time, equity))

    def _is_below_maintenance(self) -> bool:
        return self._maintenance_margin > 0.0 and self.equity / self._gross_exposure < self._maintenance_margin

    def _liquidate(self, context: Context) -> None:
        warnings.warn(
            f"LIQUIDATION at {context.bar_time.date()}: "
            f"equity/gross {self.equity / self._gross_exposure:.4f} < maintenance"
            f" margin {self._maintenance_margin:.4f}. "
            "Force-closing all positions."
        )
        for ticker, position in list(self._positions.items()):
            price = context.get_price("Close", ticker)
            if math.isnan(price):
                continue
            self._fill(Order(ticker, OrderType.MARKET, -position.size), price, context)
            self._cash -= abs(position.size * price) * self._liquidation_fee

    # def _update_orders(self, context: Context) -> None:
    #     executed_orders = []
    #
    #     for ticker, order in self._orders.items():
    #         if order.order_type == OrderType.MARKET:
    #             # TODO: check if ticker gets traded on current bar and only open a position if that is the case
    #             self._open_position(order, context)
    #             executed_orders.append(order)
    #         elif order.order_type == OrderType.LIMIT:
    #             # TODO: implement market orders
    #             pass
    #
    #     for order in executed_orders:
    #         del self._orders[order.ticker]

    # def _update_positions(self, context: Context) -> None:
    #     closed_positions = []
    #
    #     for ticker, position in self._positions.items():
    #         ordered_exit_rules = position.stop_loss_rules + position.take_profit_rules + position.timed_exit_rules
    #
    #         for exit_rule in ordered_exit_rules:
    #             if exit_rule.condition.evaluate(context, ticker):
    #
    #                 self._close_partial_position(position, exit_rule, context)
    #                 if position.size <= 0:
    #                     closed_positions.append(position)
    #                     self.closed_positions_counter += 1
    #                     break
    #
    #     for position in closed_positions:
    #         del self._positions[position.ticker]

    # TODO: check cash sufficiency before opening a position (currently positions can exceed available cash)
    # def can_open(self, order: Order, price: float) -> bool:
    #     return self._cash >= order.size * price

    # TODO: implement position scaling by making it possible to execute multiple orders on the same ticker
    # def _open_position(self, order: Order, context: Context) -> Position:
    #     price = context.get_price(order.ticker, context.bar_substep.value)
    #     total_value = order.size * price
    #     self._cash -= order.direction.sign() * total_value
    #     position = Position.from_order(order, price, context.bar_time, context.bar_num)
    #     self._positions[order.ticker] = position
    #     self.opened_positions_counter += 1
    #
    #     if PRINT_DEBUG_OUTPUT:
    #         print(
    #             f"{pd.Timestamp(context.bar_time).date()} - Opened new {position.side.name} position. "
    #             + f"Ticker: {position.ticker}, Price {price:.2f}, Size: {order.size:.2f}, "
    #             + f"Total value: {total_value:.2f}."
    #         )
    #
    #     return position

    # def _close_partial_position(self, position: Position, exit_rule: ExitRule, context: Context) -> None:
    #     if context.bar_substep == BarSubstep.OPEN:
    #         price = context.get_price(position.ticker, "Open")
    #     else:
    #         # context.bar_substep == BarSubstep.CLOSE
    #         if isinstance(exit_rule.condition, PriceCondition):
    #             price = exit_rule.condition.get_target_value(context, position.ticker)
    #         else:
    #             price = context.get_price(position.ticker, "Close")
    #
    #     if exit_rule.size_pct < position.size_pct:
    #         size_pct_to_close = exit_rule.size_pct
    #         size_to_close = exit_rule.size_pct * position.initial_size
    #         position.size -= size_to_close
    #         position.size_pct -= size_pct_to_close
    #     else:
    #         size_pct_to_close = position.size_pct
    #         size_to_close = position.size
    #         position.size = 0.0
    #         position.size_pct = 0.0
    #
    #     self._cash += position.side.sign() * size_to_close * price
    #
    #     if PRINT_DEBUG_OUTPUT:
    #         print(
    #             f"{pd.Timestamp(context.bar_time).date()} ({context.bar_substep.name}) - "
    #             + f"Closed {position.side.name} position. Reason: {exit_rule.exit_rule_type.name}, "
    #             + f"Ticker: {position.ticker}, Price {price:.2f}, Size: {size_to_close:.2f}, "
    #             + f"Total value: {size_to_close * price:.2f}."
    #         )
