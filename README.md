# bagtester

## Project Overview

backtester is a backtesting engine for stock trading strategies, written in Python. It simulates trading strategies bar
by bar using historical OHLCV data. Custom strategies are built by subclassing the `Strategy` base class, an example
strategy is included. The engine supports declarative exit rules, multi-asset portfolios, and produces equity curves
with performance metrics.

### Example Output Plot

![Sample Run Plot](assets/sample_run_plot.png)

## Features

- Bar-by-bar simulation engine with two substeps per bar (open / close)
- Strategy base class meant for subclassing, includes one example (`ShortTheGapStrategy`)
- Declarative exit rules for stop loss, take profit and timed exits
- Multi-asset simulation with concurrent positions
- Matplotlib-based analytics (equity curve, drawdown, CAGR)

## Setup & Run

### Requirements

- Python 3.11
- pip

### Linux / macOS

```bash
git clone https://github.com/lnickolay/bagtester.git
cd bagtester

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python src/main.py
```

### Windows

```bash
git clone https://github.com/lnickolay/bagtester.git
cd bagtester

py -3.11 -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python src/main.py
```

## Dependencies

- Python 3.11
- pandas, numpy, matplotlib, yfinance

## Status

Under active development. Core engine is functional, but several important features are not implemented yet, for
example:

- Opening positions via limit orders
- Transaction costs, spread & slippage
- Checks for sufficient cash or margin before accepting positions

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.
