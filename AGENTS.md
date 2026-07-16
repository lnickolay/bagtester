# bagtester

Bar-by-bar backtesting engine for short-term trading strategies, written in Python.

## Stack

- Python 3.11, pandas, numpy, matplotlib, yfinance (data ingestion)
- Strict mypy (`mypy.ini` — `disallow_untyped_defs`, `disallow_incomplete_defs`, `check_untyped_defs`, `warn_return_any`, `warn_unused_ignores`), black (120 chars)
- `from __future__ import annotations` throughout
- Dependency management via `pip-tools` (`requirements.in` → `requirements.txt`, `requirements-dev.in` → `requirements-dev.txt`)

## Architecture

```
src/main.py → Engine → DataLoader → YFinanceDataLoader (CSV)
                       Broker → Position / Order
                       Context (per-bar state)
                       Strategy (ABC) → ShortTheGapStrategy
                       Condition / Operand / ExitRule (declarative exit system)
                       analytics/evaluation.py (metrics + matplotlib plots)
```

## Key Design

- **Two substeps per bar**: `BarSubstep.OPEN` then `BarSubstep.CLOSE`. Strategy's `pre_open()` is called, then `broker.update()`, then `pre_close()`, then `broker.update()` again.
- **Declarative exit rules**: Attach `ExitRuleSpec` dataclasses (`StopLossFixedSpec`, `StopLossRatioSpec`, `TakeProfitFixedSpec`, `TakeProfitRatioSpec`, `TimedExitSpec`) to orders. These become `ExitRule` objects with `Condition` instances at position creation. Supports partial closes via `size_pct`.
- **Condition/Operand pattern**: `PriceCondition` uses smart price selection — Low for long stops, High for short stops — based on comparator direction. Conditions filter by `evaluated_substeps`.
- **`Context` object**: Assembled each substep with price/indicator data and current bar info. Provides `get_price()`, `get_indicator()`, `get_tickers()` with `bars_back` lookback.
- **Partial position closing**: `close_partial_position(size_pct)` supports fractions. Exit rules evaluated in order: stop losses → take profits → timed exits.
- **DataLoader abstraction**: `DataLoader` ABC allows plugging different data sources. `YFinanceDataLoader` reads pre-downloaded CSVs from `data/ticker_data/{source}/ohlcv_1d_max/`.
- **Two data sources**: `sample` (20 well-known tickers for fast testing) and `yfinance` (~5600 tickers for full runs).

## Module Map

| File | Purpose |
|---|---|
| `src/main.py` | Entry point — configures tickers, date range, strategy params, runs and plots |
| `src/paths.py` | `TICKER_DATA`, `TICKER_LISTS` paths; `ohclv_dir()`, `info_dir()`, `included_tickers_file()` helpers |
| `src/core/engine.py` | `Engine` — orchestrator: loads CSV data, determines union trading days, runs bar loop |
| `src/core/broker.py` | `Broker` — cash, equity, orders, positions, equity history |
| `src/core/data_loader.py` | `DataLoader` ABC, `YFinanceDataLoader` — loads OHLCV CSVs per source |
| `src/core/context.py` | `Context` — current bar state dataclass |
| `src/core/strategy.py` | `Strategy` ABC — `initialize()`, `pre_open()`, `pre_close()` |
| `src/core/order.py` | `Order` dataclass |
| `src/core/position.py` | `Position` dataclass, `from_order()` factory |
| `src/core/condition.py` | `Condition` ABC, `PriceCondition`, `LifetimeCondition` |
| `src/core/operand.py` | `Operand` ABC, `ConstantOperand`, `IndicatorOperand` |
| `src/core/exit_rule.py` | `ExitRule`, `from_spec()` factory |
| `src/core/exit_rule_spec.py` | Spec dataclasses for configuring exit rules |
| `src/core/enums.py` | `BarSubstep`, `Comparator`, `ExitRuleType`, `OrderDirection`, `OrderType`, `PositionSide` |
| `src/strategies/short_the_gap_strategy.py` | Concrete: shorts stocks gapping up at open, stop loss + same-day timed exit |
| `src/analytics/evaluation.py` | CAGR, max drawdown, matplotlib 2-panel plot |
| `src/data_ingestion/data_downloader_yfinance.py` | Downloads OHLCV from yfinance, saves CSV + JSON metadata |
| `src/_wip/config.py` | WIP: `RunConfig` dataclass + presets for CLI |
| `src/_wip/main_cli.py` | WIP: argparse CLI wrapper around simulation |
| `src/_wip/ticker_universe_generator.py` | WIP: generates ticker universe from Polygon.io files |

## Data

- `data/ticker_data/yfinance/ohlcv_1d_max/` — ~5600 CSV files (`{ticker}_1d_max.csv`), full history
- `data/ticker_data/yfinance/info/` — yfinance metadata JSONs
- `data/ticker_data/yfinance/included_tickers.txt` — flat list of all downloaded tickers (yfinance source)
- `data/ticker_data/sample/` — same structure, 20 tickers for fast dev/testing
- `data/ticker_lists/stock_universe.txt` — 5603 tickers from a filtered universe

## Project Config

- `pyproject.toml`: project metadata, black config (120 chars)
- `mypy.ini`: strict type-checking config
- `Dockerfile`: Python 3.11 + opencode-ai container, `requirements.txt` drives layer caching
- `setup.sh`: venv creation, `pip-compile`, `pip install` (supports `--global` flag for container builds)
- `.gitignore`: ignores per-source ticker data (except `sample/`), `_infos/`, `.venv/`, etc.

## Incomplete / TODOs

- LIMIT orders are stubbed (`pass` in `Broker.update_orders()`)
- No transaction costs, slippage, or spread
- No test suite
- Only one strategy implemented
- Multiple orders per ticker not supported (dict keyed by ticker)
- Establish import ordering convention and enforce with a tool (isort or ruff) for git-stable diffs
- Add `__all__` to `__init__.py` files for explicit re-exports

## Workflow

- **Source layout**: All code lives under `src/`. `src/main.py` is the entry point. Import paths are relative to `src/` (no package prefix).
- **Container setup**: Docker image with Python 3.11 venv built via `Dockerfile` (`requirements.txt` drives layer caching). Project volume-mounted. opencode runs in container, VSCode on host edits files. Rebuild image when `requirements.txt` changes.
- **Dependency workflow**: Do not install packages or edit requirements files. The user will do this manually.
- **Diff review**: opencode writes edits via volume mount, review with VSCode native Source Control diff view. Agent does not run git commit or git add; only git status and git diff for review. Human handles `git init`, staging, and commits.
- **Project note-taking**: `_infos/` directory for personal notes (gitignored). Agent can read/write there.

## Conventions

- Typed: mypy strict (`mypy.ini`), no untyped defs, no incomplete defs, warn return any
- Formatted with black at 120 chars
- Imports only used for type annotations (with `from __future__ import annotations`) go under `if TYPE_CHECKING:` to avoid circular imports and runtime overhead
- `__init__.py` files are empty (no re-exports) — import directly from the module files
