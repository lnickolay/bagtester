from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
TICKER_DATA = ROOT / "data" / "ticker_data"
TICKER_LISTS = ROOT / "data" / "ticker_lists"


def ticker_data_dir(source: str) -> Path:
    return TICKER_DATA / source


def ohclv_dir(source: str) -> Path:
    return TICKER_DATA / source / "ohlcv_1d_max"


def info_dir(source: str) -> Path:
    return TICKER_DATA / source / "info"
