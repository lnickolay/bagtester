from __future__ import annotations

import argparse
import dataclasses

import numpy as np

from _wip.config import PRESETS, RunConfig
from analytics.evaluation import show_results
from core.data_loader import YFinanceDataLoader
from core.engine import Engine
from strategies.short_the_gap_strategy import ShortTheGapStrategy


def run_simulation(config: RunConfig) -> None:
    loader = YFinanceDataLoader(source=config.source)
    tickers = loader.get_included_tickers()
    if config.ticker_count is not None:
        tickers = tickers[: config.ticker_count]

    start = np.datetime64(config.start_date)
    end = np.datetime64(config.end_date)

    engine = Engine(tickers, loader)
    strategy = ShortTheGapStrategy(engine.broker)
    engine.run_strategy(strategy, tickers, start, end)
    show_results(engine.broker, start, end)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bagtester")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    sim = subparsers.add_parser("simulate", help="Run a backtest simulation")
    sim.add_argument(
        "--preset",
        "-p",
        required=True,
        choices=list(PRESETS),
        help="Preset configuration to use",
    )
    sim.add_argument("--ticker-count", "-n", type=int, default=None)
    sim.add_argument("--start", "-s", type=str, default=None)
    sim.add_argument("--end", "-e", type=str, default=None)
    sim.add_argument("--source", type=str, default=None)

    return parser


def apply_overrides(config: RunConfig, args: argparse.Namespace) -> RunConfig:
    overrides = {}
    for field in dataclasses.fields(config):
        val = getattr(args, field.name, None)
        if val is not None:
            overrides[field.name] = val
    if overrides:
        return dataclasses.replace(config, **overrides)
    return config


def cli() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "simulate":
        config = apply_overrides(PRESETS[args.preset], args)
        run_simulation(config)


if __name__ == "__main__":
    cli()
