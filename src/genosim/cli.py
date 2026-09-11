# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Command-line interface.

    python -m genosim run    configs/baseline.yaml --outdir results/baseline
    python -m genosim sweep  configs/sweep_calibration.yaml --outdir results/sweep
    python -m genosim verify configs/baseline.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .config import load_config
from .engine import run
from .manifest import write_manifest
from .sweep import run_sweep, summarise


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    if args.seed is not None:
        from dataclasses import replace

        cfg = replace(cfg, seed=args.seed)

    df = run(cfg)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    series = outdir / "series.parquet"
    df.to_parquet(series)

    summary = outdir / "summary.json"
    summary.write_text(json.dumps(summarise(df), indent=2, sort_keys=True))

    write_manifest(outdir, cfg, [series, summary])
    print(f"run '{cfg.name}' seed={cfg.seed} -> {outdir}")
    print(json.dumps(summarise(df), indent=2, sort_keys=True))
    return 0


def _cmd_sweep(args: argparse.Namespace) -> int:
    path = run_sweep(args.config, Path(args.outdir), keep_series=args.keep_series)
    table = pd.read_csv(path)
    print(f"{len(table)} cells -> {path}")
    print(table.describe(include="all").to_string())
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    """Re-run a config twice and confirm bitwise-identical output."""
    cfg = load_config(args.config)
    a, b = run(cfg), run(cfg)
    identical = a.equals(b)
    print(f"config_hash: {cfg.content_hash()}")
    print(f"deterministic: {identical}")
    return 0 if identical else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="genosim")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="single scenario")
    p_run.add_argument("config")
    p_run.add_argument("--outdir", default="results/run")
    p_run.add_argument("--seed", type=int, default=None)
    p_run.set_defaults(func=_cmd_run)

    p_sweep = sub.add_parser("sweep", help="parameter grid")
    p_sweep.add_argument("config")
    p_sweep.add_argument("--outdir", default="results/sweep")
    p_sweep.add_argument("--keep-series", action="store_true")
    p_sweep.set_defaults(func=_cmd_sweep)

    p_ver = sub.add_parser("verify", help="check determinism")
    p_ver.add_argument("config")
    p_ver.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
