from __future__ import annotations

import warnings
from collections import defaultdict
from typing import TYPE_CHECKING

import pandas as pd

from core.enums import OrderStatus, OrderType
from core.order import Order
from core.position import Position

if TYPE_CHECKING:
    from core.context import Context


class Broker:

    _cash: float
    equity: float
    _initial_equity: float
    _equity_history: list[tuple[pd.Timestamp, float]]
    _gross_exposure: float

    _submitted_orders: list[Order]
    _scheduled_orders: list[Order]
    _executable_orders: list[Order]
    _conditional_orders: list[Order]
    _positions: dict[str, Position]

    _initial_margin: float
    _maintenance_margin: float
    _liquidation_fee: float

    # TODO: track opened and closed positions etc differently
    opened_positions_counter: int
    closed_positions_counter: int

    def __init__(
        self, cash: float, initial_margin: float = 1.0, maintenance_margin: float = 0.0, liquidation_fee: float = 0.0
    ) -> None:
        self._cash = cash
        self.equity = cash
        self._initial_equity = cash
        self._equity_history = []
        self._gross_exposure = 0.0

        self._submitted_orders = []
        self._scheduled_orders = []
        self._executable_orders = []
        self._conditional_orders = []
        self._positions = {}

        self._initial_margin = initial_margin
        self._maintenance_margin = maintenance_margin
        self._liquidation_fee = liquidation_fee

        self.opened_positions_counter = 0
        self.closed_positions_counter = 0

    def get_equity_series(self) -> pd.Series:
        bar_timeline, equities = zip(*self._equity_history)
        return pd.Series(equities, index=bar_timeline)

    def get_position(self, ticker: str) -> Position | None:
        return self._positions.get(ticker)

    def submit_order(self, order: Order) -> None:
        self._submitted_orders.append(order)

    def update(self, context: Context) -> None:
        self._update_equity_and_gross_exposure(context, "Open")

        self._handle_submitted_orders(context)
        self._handle_scheduled_orders(context)
        self._handle_executable_orders(context)
        self._handle_conditional_orders(context)

        self._update_equity_and_gross_exposure(context, "Close")
        if self._is_below_maintenance():
            self._liquidate(context)
            self._update_equity_and_gross_exposure(context, "Close")

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

    def _handle_submitted_orders(self, context: Context) -> None:
        for order in self._submitted_orders:
            if order.has_expired_at(context.bar_time):
                order.status = OrderStatus.EXPIRED
                continue

            order.status = OrderStatus.ACCEPTED
            if order.valid_from_bars is not None:
                order.valid_from_time = context.bar_timeline[
                    min(context.bar_num + order.valid_from_bars, len(context.bar_timeline) - 1)
                ]
            if order.valid_until_bars is not None:
                order.valid_until_time = context.bar_timeline[
                    min(context.bar_num + order.valid_until_bars, len(context.bar_timeline) - 1)
                ]
            if order.is_scheduled_at(context.bar_time):
                self._scheduled_orders.append(order)
            elif order.order_type == OrderType.MARKET:
                self._executable_orders.append(order)
            else:
                self._conditional_orders.append(order)
        self._submitted_orders.clear()

    def _handle_scheduled_orders(self, context: Context) -> None:
        # TODO: use binary heap instead or not worth it?
        self._scheduled_orders.sort(key=lambda o: o.valid_from_time)  # type: ignore[arg-type]
        remaining = []
        for order in self._scheduled_orders:
            if order.status != OrderStatus.ACCEPTED:
                continue
            if not order.is_scheduled_at(context.bar_time):
                if order.order_type == OrderType.MARKET:
                    self._executable_orders.append(order)
                else:
                    self._conditional_orders.append(order)
            else:
                remaining.append(order)
        self._scheduled_orders = remaining

    def _handle_executable_orders(self, context: Context) -> None:
        # NOTE: orders are grouped by ticker here so that only one margin check per ticker on the net result is needed,
        # this changes the execution order of the immediate orders
        ticker_to_orders: dict[str, list[Order]] = defaultdict(list)
        for order in self._executable_orders:
            if order.status == OrderStatus.ACCEPTED:
                ticker_to_orders[order.ticker].append(order)
        self._executable_orders.clear()

        for ticker, orders in ticker_to_orders.items():
            price = context.get_price("Open", ticker)
            if pd.isna(price):
                continue
            net_size = sum(order.size for order in orders)
            if self._passes_initial_margin(ticker, net_size, price):
                for order in orders:
                    self._fill(order, price, context)

    def _handle_conditional_orders(self, context: Context) -> None:
        self._conditional_orders.sort(key=lambda o: o.role.value, reverse=True)

        remaining = []
        for order in self._conditional_orders:
            if order.status != OrderStatus.ACCEPTED:
                continue
            if order.has_expired_at(context.bar_time):
                order.status = OrderStatus.EXPIRED
                continue

            fill_price = self._determine_conditional_order_fill_price(order, context)
            if fill_price is None:
                remaining.append(order)
            elif not self._passes_initial_margin(order.ticker, order.size, fill_price):
                order.status = OrderStatus.REJECTED
            else:
                self._fill(order, fill_price, context)

        self._conditional_orders = remaining

    def _determine_conditional_order_fill_price(self, order: Order, context: Context) -> float | None:
        if order.order_type == OrderType.LIMIT:
            trigger_if_greq = order.size < 0.0
            trigger_price = order.limit_price
        elif order.order_type == OrderType.STOP:
            trigger_if_greq = order.size > 0.0
            trigger_price = order.stop_price
        else:
            return None

        assert trigger_price is not None
        open_price = context.get_price("Open", order.ticker)
        # TODO: add Context helper method for checking if ticker traded on current bar
        if pd.isna(open_price):
            return None
        high_price = context.get_price("High", order.ticker)
        low_price = context.get_price("Low", order.ticker)
        fill_price = None

        if trigger_if_greq:
            if open_price >= trigger_price:
                fill_price = open_price
            elif high_price >= trigger_price:
                fill_price = trigger_price
        else:
            if open_price <= trigger_price:
                fill_price = open_price
            elif low_price <= trigger_price:
                fill_price = trigger_price

        return fill_price

    def _fill(self, order: Order, price: float, context: Context) -> None:
        order.status = OrderStatus.FILLED
        self._gross_exposure += self._calc_gross_delta(order.ticker, order.size, price)
        self._cash -= order.size * price

        for child in order.child_orders:
            self.submit_order(child)

        self._cancel_siblings(order)

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

    def _cancel_siblings(self, order: Order) -> None:
        if order.parent_order is not None:
            for sibling_order in order.parent_order.child_orders:
                if sibling_order is not order and sibling_order.status == OrderStatus.ACCEPTED:
                    sibling_order.status = OrderStatus.CANCELED

    def _passes_initial_margin(self, ticker: str, size: float, price: float) -> bool:
        new_gross = self._gross_exposure + self._calc_gross_delta(ticker, size, price)
        if new_gross > 0 and self.equity / new_gross < self._initial_margin:
            warnings.warn("MARGIN BREACH: Order exceeds initial margin. Rejected.")
            return False
        else:
            return True

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
            if pd.isna(price):
                continue
            self._fill(Order(ticker, OrderType.MARKET, -position.size), price, context)
            self._cash -= abs(position.size * price) * self._liquidation_fee

    def _calc_gross_delta(self, ticker: str, size: float, price: float) -> float:
        existing_position = self._positions.get(ticker)
        existing_size = existing_position.size if existing_position is not None else 0.0
        return price * (abs(existing_size + size) - abs(existing_size))

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
