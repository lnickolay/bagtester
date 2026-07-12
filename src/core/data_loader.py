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
        # TODO: possibly rename runtime measurement variables
        load_start_time = time.perf_counter()
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
            df["Date"] = pd.to_datetime(df["Date"], utc=True, errors="coerce")
            # remove timezone
            df["Date"] = df["Date"].dt.tz_convert(None)
            # set date as index (useful for backtesting)
            df.set_index("Date", inplace=True)

            price_data[ticker] = df

            if i % 100 == 0:
                print(f"Progress: {i}/{len(tickers)} assets loaded.")

        load_duration = time.perf_counter() - load_start_time
        print(
            f"Finished loading OHLCV data for {len(tickers)} assets. "
            + f"Total time required to load data: {load_duration:.1f}s"
        )
        print("-" * 10)

        return price_data

    def get_included_tickers(self) -> list[str]:
        with open(included_tickers_file(self._source)) as f:
            return [line.strip() for line in f if line.strip()]
