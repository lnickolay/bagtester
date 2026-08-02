# bagtester Project Info

bagtester is a simple backtesting engine for stock and crypto trading strategies.

## Tech Stack

- **Python**: Python 3.11
- **Python libraries**: matplotlib, numpy, pandas, yfinance
- **Python development tools**: black, mypy, pip-tools, pytest
- **Other development tools**: OpenCode, Docker

## Repo Contents

- `src/` — application runtime code
- `inttests/` — integration tests (one subdir per inttest)
- `data/` — OHLCV data, ticker lists, metadata
- `_notes/` — notes on project design, planned features, TODOs etc.

## Development Rules

- Treat `src/` as the source root. Import modules without the `src.` prefix.
- `src/main.py` is the application entry point.
- Do not install packages or modify dependency files.
- Only use read-only git commands (for example `git status` and `git diff`). Do not run any git command that changes the repository or working tree.
- Always use Black formatting.
- Add type annotations so the code is valid under `mypy --strict`.
- Do not run tests or lint/style checks during development. The user will run these manually.
- Follow Python underscore visibility: public API has no prefix, implementation details use single `_` prefix.
- Never import a type at runtime if it is only used for type annotations. Put those imports under `if TYPE_CHECKING:`.
- Never add imports or re-exports to `__init__.py`. Leave `__init__.py` empty.
- Keep `_notes/` updated when discussing or working on topics related to the notes contained therein.
- In notes and documentation, put all class/method/attribute names and code references in backticks (e.g. `_fill`, `Strategy.buy()`, `Order.size`). Method/function names get `()` suffix.
- Output text that includes descriptive prose should be written as a full sentence ending with appropriate punctuation. Bare value dumps for debugging are exempt.
