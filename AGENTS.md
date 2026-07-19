# bagtester Project Info

bagtester is a simple backtesting engine for stock and crypto trading strategies.

## Tech Stack

- **Python**: Python 3.11
- **Python libraries**: matplotlib, numpy, pandas, yfinance
- **Python development tools**: black, mypy, pip-tools
- **Other development tools**: OpenCode, Docker

## Development Rules

- All source code belongs under `src/`.
- Treat `src/` as the source root. Import modules without the `src.` prefix.
- `src/main.py` is the application entry point.
- Do not install packages or modify dependency files.
- Only use read-only git commands (for example `git status` and `git diff`). Do not run any git command that changes the repository or working tree.
- `_infos/` contains manual project notes for the user. Ignore this directory.
- Always use Black formatting.
- Add type annotations so the code is valid under `mypy --strict`.
- Never import a type at runtime if it is only used for type annotations. Put those imports under `if TYPE_CHECKING:`.
- Never add imports or re-exports to `__init__.py`. Leave `__init__.py` empty.

## Repo Contents

Keep this section up to date. Whenever you add, remove, rename, move, or materially change the purpose of a listed file or module, update the corresponding entry as part of the same change.

### Source Code

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

### Input Data

| File | Purpose |
|---|---|
| `data/ticker_data/yfinance/ohlcv_1d_max/` | ~5600 CSV files (`{ticker}_1d_max.csv`), full history |
| `data/ticker_data/yfinance/info/` | yfinance metadata JSONs |
| `data/ticker_data/yfinance/included_tickers.txt` | Flat list of all downloaded tickers (yfinance source) |
| `data/ticker_data/sample/` | Same structure, 20 tickers for fast dev/testing |
| `data/ticker_lists/stock_universe.txt` | 5603 tickers from a filtered universe |

### Project Config

| File | Purpose |
|---|---|
 | `pyproject.toml` | Project metadata, black config |
| `mypy.ini` | Strict type-checking config |
| `Dockerfile` | Python 3.11 + opencode-ai container, `requirements.txt` drives layer caching |
| `setup.sh` | Venv creation, `pip-compile`, `pip install` (supports `--global` flag for container builds) |
| `.gitignore` | Ignores per-source ticker data (except `sample/`), `_infos/`, `.venv/`, etc. |
