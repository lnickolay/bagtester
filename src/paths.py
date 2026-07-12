from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TICKER_DATA = ROOT / "data" / "ticker_data"
TICKER_LISTS = ROOT / "data" / "ticker_lists"


def ohclv_dir(source: str) -> Path:
    return TICKER_DATA / source / "ohlcv_1d_max"


def info_dir(source: str) -> Path:
    return TICKER_DATA / source / "info"


def included_tickers_file(source: str) -> Path:
    return TICKER_DATA / source / "included_tickers.txt"
