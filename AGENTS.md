# bagtester

Bar-by-bar backtesting engine for short-term trading strategies, written in Python.

## Stack

- Python 3.11, pandas, numpy, matplotlib, yfinance (data ingestion)
- Strict mypy (`disallow_untyped_defs = True`), black (120 chars)
- `from __future__ import annotations` throughout

## Architecture

```
main.py → Engine → Broker → Position / Order
                  → Context (per-bar state)
                  → Strategy (ABC) → ShortTheGapStrategy
                  → Condition / Operand / ExitRule (declarative exit system)
                  → analytics/evaluation.py (metrics + matplotlib plots)
```

## Key Design

- **Two substeps per bar**: `BarSubstep.OPEN` then `BarSubstep.CLOSE`. Strategy's `pre_open()` is called, then `broker.update()`, then `pre_close()`, then `broker.update()` again.
- **Declarative exit rules**: Attach `ExitRuleSpec` dataclasses (`StopLossFixedSpec`, `StopLossRatioSpec`, `TakeProfitFixedSpec`, `TakeProfitRatioSpec`, `TimedExitSpec`) to orders. These become `ExitRule` objects with `Condition` instances at position creation. Supports partial closes via `size_pct`.
- **Condition/Operand pattern**: `PriceCondition` uses smart price selection — Low for long stops, High for short stops — based on comparator direction. Conditions filter by `evaluated_substeps`.
- **`Context` object**: Assembled each substep with price/indicator data and current bar info. Provides `get_price()`, `get_indicator()`, `get_tickers()` with `bars_back` lookback.
- **Partial position closing**: `close_partial_position(size_pct)` supports fractions. Exit rules evaluated in order: stop losses → take profits → timed exits.

## Module Map

| File | Purpose |
|---|---|
| `core/engine.py` | `Engine` — orchestrator: loads CSV data, determines union trading days, runs bar loop |
| `core/broker.py` | `Broker` — cash, equity, orders, positions, equity history |
| `core/context.py` | `Context` — current bar state dataclass |
| `core/strategy.py` | `Strategy` ABC — `initialize()`, `pre_open()`, `pre_close()` |
| `core/order.py` | `Order` dataclass |
| `core/position.py` | `Position` dataclass, `from_order()` factory |
| `core/condition.py` | `Condition` ABC, `PriceCondition`, `LifetimeCondition` |
| `core/operand.py` | `Operand` ABC, `ConstantOperand`, `IndicatorOperand` |
| `core/exit_rule.py` | `ExitRule`, `from_spec()` factory |
| `core/exit_rule_spec.py` | Spec dataclasses for configuring exit rules |
| `core/enums.py` | `BarSubstep`, `Comparator`, `ExitRuleType`, `OrderDirection`, `OrderType`, `PositionSide` |
| `strategies/short_the_gap_strategy.py` | Concrete: shorts stocks gapping up at open, stop loss + same-day timed exit |
| `analytics/evaluation.py` | CAGR, max drawdown, matplotlib 2-panel plot |
| `data_ingestion/stocks_data_downloader_yfinance.py` | Downloads OHLCV from yfinance, saves CSV + JSON metadata |
| `constants.py` | Paths, DEBUG flag |
| `main.py` | Entry point — configures tickers, date range, strategy params, runs and plots |

## Data

- `assets/stock_data/ohlcv_1d_max/` — ~5600 CSV files (`{ticker}_1d_max.csv`), one per ticker, full history
- `assets/stock_data/info/` — yfinance metadata JSONs
- `assets/ticker_lists/massive/` — ticker lists from Polygon.io format (cs1-6.json, adrc.json)
- `downloaded_ticker_symbols.txt` — flat list of all downloaded tickers

## Incomplete / TODOs

- LIMIT orders are stubbed (`pass` in `Broker.update_orders()`)
- No transaction costs, slippage, or spread
- No test suite
- Only one strategy implemented
- Multiple orders per ticker not supported (dict keyed by ticker)
- Need to translate German comments to English before publishing
- Establish import ordering convention and enforce with a tool (isort or ruff) for git-stable diffs

## Workflow

- **Container setup**: Docker image with Python venv built in Dockerfile (`requirements.txt` drives layer caching). Project volume-mounted. opencode runs in container, VSCode on host edits files. Rebuild image when `requirements.txt` changes.
  A separate host-side venv exists for manual dev work. Only ever `pip install` on the host — update `requirements.in` manually, then rebuild `requirements.txt` so the Docker layer cache picks it up on next build.
- **Diff review**: `git init && git add -A && git commit -m "init"` for baseline. opencode writes edits via volume mount, review with VSCode native Source Control diff view. `rm -rf .git` when ready for fresh repo.
- **Project note-taking**: Some persistent place for todos, decisions, notes the agent can read/write. Could be a file in the repo, or an Obsidian vault dir mounted into the container.

## Conventions

- Typed: mypy strict, no untyped defs, no incomplete defs, warn return any
- Formatted with black at 120 chars
- German developer — some comments in German
- Imports only used for type annotations (with `from __future__ import annotations`) go under `if TYPE_CHECKING:` to avoid circular imports and runtime overhead.
