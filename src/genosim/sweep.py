# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Parameter sweeps.

Parameter-insensitivity is a claim, and a claim needs a result surface, not
a single run. This module takes a base config plus a grid over any nested
parameter path and produces one row of summary metrics per cell, with the
full raw series retained per cell if requested.

Grid spec in YAML:

    sweep:
      mechanism.theta_max: [2.0, 3.0, 4.0, 5.0]
      mechanism.geno_burn_rate: [0.01, 0.02, 0.05]
      seed: [1, 2, 3, 4, 5]

Every combination is run. Seeds are part of the grid so that a cell's
variation across seeds can be separated from variation across parameters --
without that, a sweep cannot distinguish a fragile parameter from noise.
"""

from __future__ import annotations

import itertools
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
import yaml

from .config import RunConfig, load_config
from .engine import run


def _set_path(cfg: RunConfig, dotted: str, value: Any) -> RunConfig:
    """Return a new config with one nested field replaced. Configs are frozen."""
    parts = dotted.split(".")
    if len(parts) == 1:
        return replace(cfg, **{parts[0]: value})
    if len(parts) == 2:
        section, field = parts
        sub = getattr(cfg, section)
        return replace(cfg, **{section: replace(sub, **{field: value})})
    raise ValueError(f"unsupported parameter path: {dotted}")


def expand_grid(cfg: RunConfig, grid: dict[str, list[Any]]) -> Iterator[RunConfig]:
    """Yield one config per grid cell, in deterministic (sorted) order."""
    keys = sorted(grid)
    for combo in itertools.product(*(grid[k] for k in keys)):
        out = cfg
        for key, value in zip(keys, combo):
            out = _set_path(out, key, value)
        label = ",".join(f"{k}={v}" for k, v in zip(keys, combo))
        yield replace(out, name=f"{cfg.name}[{label}]")


def summarise(df: pd.DataFrame) -> dict[str, float]:
    """Collapse one run to the metrics that decide whether the design holds.

    Add your own. These are the ones that matter for a redemption-backed
    design: does the floor hold, does the backing ratio stay above 1, and
    does the governor settle or oscillate.
    """
    return {
        "final_price": float(df["price"].iloc[-1]),
        "min_price": float(df["price"].min()),
        "min_backing_ratio": float(df["backing_ratio"].min()),
        "final_backing_ratio": float(df["backing_ratio"].iloc[-1]),
        "floor_breached": bool(df["floor_breached"].any()),
        "max_velocity": float(df["velocity"].max()),
        "velocity_std_last_quarter": float(
            df["velocity"].iloc[-len(df) // 4:].std()
        ),
        "price_drawdown": float(
            1.0 - df["price"].min() / max(df["price"].max(), 1e-12)
        ),
    }


def run_sweep(config_path: str | Path, outdir: Path, keep_series: bool = False) -> Path:
    """Run every grid cell and write a tidy results table."""
    config_path = Path(config_path)
    base = load_config(config_path)
    raw = yaml.safe_load(config_path.read_text())
    grid = raw.get("sweep")
    if not grid:
        raise ValueError(f"{config_path} has no 'sweep:' block")

    outdir.mkdir(parents=True, exist_ok=True)
    series_dir = outdir / "series"
    if keep_series:
        series_dir.mkdir(exist_ok=True)

    rows = []
    for i, cell in enumerate(expand_grid(base, grid)):
        df = run(cell)
        record = {"cell": cell.name, "seed": cell.seed, **summarise(df)}
        rows.append(record)
        if keep_series:
            df.to_parquet(series_dir / f"cell_{i:05d}.parquet")

    table = pd.DataFrame(rows)
    path = outdir / "sweep_results.csv"
    table.to_csv(path, index=False)
    return path
