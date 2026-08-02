import json
import time
from pathlib import Path

import yfinance as yf

import paths


def _load_tickers(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def _download_stock_data_yfinance(tickers: list[str]) -> None:

    downloaded_tickers = []

    print(f"Downloading stock data for {len(tickers)} stocks from yahoo finance.")
    print("-" * 10)

    for i, ticker in enumerate(tickers, start=1):

        if (paths.ohclv_dir("yfinance") / f"{ticker}_1d_max.csv").is_file():
            # TODO: implement possibility to append newer data to existing files (or at least overwrite them)?
            print(f"Ticker {ticker} already downloaded! ({i}/{len(tickers)})")
            continue

        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        # ohlcv_1d_max_df = yf_ticker.history(period="max", interval="1d")
        ohlcv_1d_max_df = yf_ticker.history(start="2000-01-01", end="2026-01-01", interval="1d")

        if not ohlcv_1d_max_df.empty:
            ohlcv_1d_max_df.to_csv(paths.ohclv_dir("yfinance") / f"{ticker}_1d_max.csv")
            with open(paths.info_dir("yfinance") / f"{ticker}_info.json", "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=4)
            print(f"Ticker {ticker} saved! ({i}/{len(tickers)})")
            downloaded_tickers.append(ticker)
        else:
            print(f"No data for Ticker {ticker} found! ({i}/{len(tickers)})")

        if i % 100 == 0:
            time.sleep(10)

    # TODO: the log message incorrectly counts already downloaded stocks as missing
    print("-" * 10)
    print(
        f"Downloaded stock data for {len(downloaded_tickers)} out of {len(tickers)} stocks from yahoo "
        + f"finance. Stock data for {len(tickers) - len(downloaded_tickers)} could not be found."
    )

    with open(paths.ticker_data_dir("yfinance") / "included_tickers.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(downloaded_tickers) + "\n")


if __name__ == "__main__":
    tickers = _load_tickers(paths.TICKER_LISTS / "stock_universe.txt")
    # tickers = tickers[:100]
    _download_stock_data_yfinance(tickers)
