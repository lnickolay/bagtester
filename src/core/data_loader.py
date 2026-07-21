from __future__ import annotations

import time
from abc import ABC, abstractmethod

import pandas as pd

from paths import TICKER_DATA, included_tickers_file


class DataLoader(ABC):

    def __init__(self, source: str) -> None:
        # TODO: check if one of these attributes can be removed
        self._source = source
        self._root = TICKER_DATA / source

    @abstractmethod
    def load_price_data(self, tickers: list[str]) -> dict[str, pd.DataFrame]: ...

    @abstractmethod
    def get_included_tickers(self) -> list[str]: ...


class YFinanceDataLoader(DataLoader):

    def __init__(self, source: str = "yfinance") -> None:
        super().__init__(source)

    def load_price_data(self, tickers: list[str]) -> dict[str, pd.DataFrame]:
        load_timer_start = time.perf_counter()
        print(f"Loading OHLCV data for {len(tickers)} assets.")

        price_data: dict[str, pd.DataFrame] = {}

        for i, ticker in enumerate(tickers, start=1):
            df = pd.read_csv(
                self._root / "ohlcv_1d_max" / f"{ticker}_1d_max.csv",
                dtype={
                    "Date": str,
                    "Open": float,
                    "High": float,
                    "Low": float,
                    "Close": float,
                    "Volume": int,
                    "Dividends": float,
                    "Stock Splits": float,
                },
            )
            df.rename(columns={"Date": "Time"}, inplace=True)
            df["Time"] = pd.to_datetime(df["Time"], utc=True, errors="coerce")
            # remove timezone
            df["Time"] = df["Time"].dt.tz_convert(None)
            df.set_index("Time", inplace=True)

            price_data[ticker] = df

            if i % 100 == 0:
                print(f"Progress: {i}/{len(tickers)} assets loaded.")

        load_timer_elapsed = time.perf_counter() - load_timer_start
        print(
            f"Finished loading OHLCV data for {len(tickers)} assets. "
            + f"Total time required to load data: {load_timer_elapsed:.1f}s"
        )
        print("-" * 10)

        return price_data

    def get_included_tickers(self) -> list[str]:
        with open(included_tickers_file(self._source)) as f:
            return [line.strip() for line in f if line.strip()]
