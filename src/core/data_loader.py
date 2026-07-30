from __future__ import annotations

import time
from abc import ABC, abstractmethod

import pandas as pd

from paths import ohclv_dir, ticker_data_dir


class DataLoader(ABC):

    def __init__(self, source: str) -> None:
        self._source = source

    @abstractmethod
    def load_price_data(
        self,
        tickers: list[str],
        start_time: pd.Timestamp | None = None,
        end_time: pd.Timestamp | None = None,
    ) -> dict[str, pd.DataFrame]: ...

    @abstractmethod
    def get_included_tickers(self) -> list[str]: ...


class YFinanceDataLoader(DataLoader):

    def __init__(self, source: str = "yfinance") -> None:
        super().__init__(source)

    def load_price_data(
        self,
        tickers: list[str],
        start_time: pd.Timestamp | None = None,
        end_time: pd.Timestamp | None = None,
    ) -> dict[str, pd.DataFrame]:
        load_timer_start = time.perf_counter()
        print(f"Loading OHLCV data for {len(tickers)} assets.")

        price_data: dict[str, pd.DataFrame] = {}

        for i, ticker in enumerate(tickers, start=1):
            df = pd.read_csv(
                ohclv_dir(self._source) / f"{ticker}_1d_max.csv",
                usecols=["Date", "Open", "High", "Low", "Close", "Volume"],
                dtype={
                    "Date": str,
                    "Open": float,
                    "High": float,
                    "Low": float,
                    "Close": float,
                    "Volume": int,
                },
            )
            df.rename(columns={"Date": "Time"}, inplace=True)
            df["Time"] = pd.to_datetime(df["Time"], utc=True, errors="coerce")
            # remove timezone
            df["Time"] = df["Time"].dt.tz_convert(None)
            df.set_index("Time", inplace=True)

            price_data[ticker] = df.loc[start_time:end_time]

            if i % 100 == 0:
                print(f"Progress: {i}/{len(tickers)} assets loaded.")

        load_timer_elapsed = time.perf_counter() - load_timer_start
        print(
            f"Finished loading OHLCV data for {len(tickers)} assets. "
            + f"Total time required to load data: {load_timer_elapsed:.1f}s"
        )
        print("-" * 10)

        return price_data

    def get_included_tickers(self, include_blacklisted: bool = False) -> list[str]:
        included_tickers = (ticker_data_dir(self._source) / "included_tickers.txt").read_text().splitlines()

        if not include_blacklisted:
            blacklisted_file = ticker_data_dir(self._source) / "blacklisted_tickers.txt"
            if blacklisted_file.exists():
                blacklisted_tickers = set(blacklisted_file.read_text().splitlines())
                return [ticker for ticker in included_tickers if ticker not in blacklisted_tickers]

        return included_tickers
