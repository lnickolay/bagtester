import os.path
from glob import glob

from massive import RESTClient


def generate_ticker_universe():
    tickers = []
    for t in client.list_tickers(
        type="CS",
        market="stocks",
        date="2025-12-31",
        active="true",
        order="asc",
        limit="1000",
        sort="ticker",
    ):
        tickers.append(t)

    ...

    ticker_universe = []
    included_ticker_types = ["cs", "adrc"]

    for ticker_type in included_ticker_types:
        for path in glob(os.path.join(f"ticker_lists/massive/{ticker_type}", "*.json")):
            with open(path, "r", encoding="utf8") as f:
                tickers_json = json.load(f)
                ticker_universe.extend(item["ticker"] for item in tickers_json["results"])

    ticker_universe.sort()
    # print(ticker_universe)
    # print(len(ticker_universe))

    # ticker_universe = ticker_universe[:50]
