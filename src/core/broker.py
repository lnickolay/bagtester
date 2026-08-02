from __future__ import annotations

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

    _maker_fee: float
    _taker_fee: float
    _market_order_slippage: float
    _stop_order_slippage: float
    _liquidation_fee: float

    # TODO: track opened and closed positions etc differently
    opened_positions_counter: int
    closed_positions_counter: int

    def __init__(
        self,
        initial_cash: float = 10000.0,
        initial_margin: float = 1.0,
        maintenance_margin: float = 0.0,
        commission: float = 0.0,
        maker_fee: float = 0.0,
        taker_fee: float = 0.0,
        market_order_slippage: float = 0.0,
        stop_order_slippage: float = 0.0,
        liquidation_fee: float = 0.0,
    ) -> None:
        self._cash = initial_cash
        self.equity = initial_cash
        self._initial_equity = initial_cash
        self._equity_history = []
        self._gross_exposure = 0.0

        self._initial_margin = initial_margin
        self._maintenance_margin = maintenance_margin

        if commission != 0.0:
            if maker_fee != 0.0 or taker_fee != 0.0:
                raise ValueError("Either commissions or maker/taker should be specified, not both.")
            self._maker_fee = self._taker_fee = commission
        else:
            self._maker_fee = maker_fee
            self._taker_fee = taker_fee
        self._market_order_slippage = market_order_slippage
        self._stop_order_slippage = stop_order_slippage
        self._liquidation_fee = liquidation_fee

        self._submitted_orders = []
        self._scheduled_orders = []
        self._executable_orders = []
        self._conditional_orders = []
        self._positions = {}

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
        # second _handle_submitted_orders() call here so that child TP/SL limit orders of parent orders triggered at
        # open can get triggered on the same bar
        self._handle_submitted_orders(context)
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
        self._scheduled_orders.sort(key=lambda order: order.valid_from_time)  # type: ignore[arg-type]
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
        self._executable_orders.sort(key=lambda order: 0 if self._calc_gross_size_delta(order) < 0.0 else 1)
        for order in self._executable_orders:
            if order.status != OrderStatus.ACCEPTED:
                continue

            price = context.get_price("Open", order.ticker)
            if not pd.isna(price):
                self._try_execution(order, price, context)
            else:
                order.status = OrderStatus.REJECTED
        self._executable_orders.clear()

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
            if fill_price is not None:
                self._try_execution(order, fill_price, context)
            else:
                remaining.append(order)
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

    def _try_execution(self, order: Order, base_price: float, context: Context, is_liquidation: bool = False) -> None:
        sign = 1.0 if order.size > 0.0 else -1.0
        if order.order_type == OrderType.MARKET:
            fee = self._taker_fee
            slippage = self._market_order_slippage
        elif order.order_type == OrderType.STOP:
            fee = self._taker_fee
            slippage = self._stop_order_slippage
        else:
            fee = self._maker_fee
            slippage = 0.0
        fill_price = base_price * (1.0 + slippage * sign)

        existing_position = self._positions.get(order.ticker)
        existing_size = existing_position.size if existing_position is not None else 0.0
        gross_exposure_delta = self._calc_gross_size_delta(order) * fill_price

        fee_cost = abs(order.size * fill_price) * fee
        if not is_liquidation:
            if self.equity - fee_cost < self._initial_margin * (self._gross_exposure + gross_exposure_delta):
                print("MARGIN BREACH: Order exceeds initial margin requirement. Rejected.")
                order.status = OrderStatus.REJECTED
                return
        else:
            fee_cost += abs(order.size * fill_price) * self._liquidation_fee

        order.status = OrderStatus.FILLED
        for child in order.child_orders:
            self.submit_order(child)
        self._cancel_siblings(order)

        self._cash -= order.size * fill_price + fee_cost
        self.equity -= fee_cost
        self._gross_exposure += gross_exposure_delta

        new_size = existing_size + order.size
        if existing_position is None:
            self._positions[order.ticker] = Position(
                ticker=order.ticker,
                size=new_size,
                avg_price=fill_price,
                entry_bar_time=context.bar_time,
                entry_bar_num=context.bar_num,
            )
            self.opened_positions_counter += 1
        elif new_size == 0.0:
            del self._positions[order.ticker]
            self.closed_positions_counter += 1
        elif (existing_position.size > 0.0) == (new_size > 0.0):
            if abs(new_size) > abs(existing_position.size):
                existing_position.avg_price = (
                    existing_position.avg_price * existing_position.size + fill_price * order.size
                ) / new_size
            existing_position.size = new_size
        else:
            del self._positions[order.ticker]
            self.closed_positions_counter += 1
            self._positions[order.ticker] = Position(
                ticker=order.ticker,
                size=new_size,
                avg_price=fill_price,
                entry_bar_time=context.bar_time,
                entry_bar_num=context.bar_num,
            )
            self.opened_positions_counter += 1

    def _calc_gross_size_delta(self, order: Order) -> float:
        existing_position = self._positions.get(order.ticker)
        existing_size = existing_position.size if existing_position is not None else 0.0
        return abs(existing_size + order.size) - abs(existing_size)

    def _cancel_siblings(self, order: Order) -> None:
        if order.parent_order is not None:
            for sibling_order in order.parent_order.child_orders:
                if sibling_order is not order and sibling_order.status == OrderStatus.ACCEPTED:
                    sibling_order.status = OrderStatus.CANCELED

    def _is_below_maintenance(self) -> bool:
        return self._maintenance_margin > 0.0 and self.equity < self._maintenance_margin * self._gross_exposure

    def _liquidate(self, context: Context) -> None:
        print("LIQUIDATION: Equity below maintenance margin requirement. Force-closing all positions.")
        for ticker, position in list(self._positions.items()):
            price = context.get_price("Close", ticker)
            if not pd.isna(price):
                liquidation_order = Order(ticker, OrderType.MARKET, -position.size)
                self._try_execution(liquidation_order, price, context, is_liquidation=True)
