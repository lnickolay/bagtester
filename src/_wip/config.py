from __future__ import annotations

from dataclasses import dataclass

DEBUG = False


@dataclass
class RunConfig:
    source: str = "yfinance"
    ticker_count: int | None = None
    start_date: str = "2020-01-01"
    end_date: str = "2024-12-31"


PRESETS: dict[str, RunConfig] = {
    "sample": RunConfig(source="sample"),
    "quick": RunConfig(ticker_count=100),
    "medium": RunConfig(ticker_count=1000),
    "full": RunConfig(),
    "full-2025": RunConfig(start_date="2025-01-01", end_date="2025-12-31"),
}
