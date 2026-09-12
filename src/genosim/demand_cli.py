# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""CLI for the demand model.

    python -m genosim.demand_cli run    configs/demand/em_high_inflation.yaml
    python -m genosim.demand_cli sweep  configs/demand/sweep_uncertainty.yaml
    python -m genosim.demand_cli verify configs/demand/em_high_inflation.yaml
    python -m genosim.demand_cli aggregate --years 10
"""
from __future__ import annotations

import argparse, itertools, json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .demand import run_demand, summarise_demand
from .demand_config import (content_hash, load_demand_config, load_sweep_grid,
                            set_path, to_dict)

from .pools import aggregate, provenance_table


def _write(outdir: Path, cfg, df):
    outdir.mkdir(parents=True, exist_ok=True)
    series = outdir / "series.parquet"; df.to_parquet(series)
    summary = outdir / "summary.json"
    summary.write_text(json.dumps(summarise_demand(df), indent=2, sort_keys=True))
    cfgfile = outdir / "config_resolved.json"
    cfgfile.write_text(json.dumps(
        {"config_hash": content_hash(cfg), "config": to_dict(cfg)},
        indent=2, sort_keys=True))
    return [series, summary, cfgfile]


def _cmd_run(a):
    cfg = load_demand_config(a.config)
    if a.seed is not None:
        cfg = replace(cfg, seed=a.seed)
    df = run_demand(cfg)
    out = Path(a.outdir)
    files = _write(out, cfg, df)
    try:
        pass
    except Exception:
        pass  # manifest expects RunConfig; config_resolved.json carries provenance
    print(f"{cfg.name} seed={cfg.seed} hash={content_hash(cfg)[:12]} -> {out}")
    print(json.dumps(summarise_demand(df), indent=2, sort_keys=True))
    return 0


def _cmd_sweep(a):
    cfg = load_demand_config(a.config)
    grid = load_sweep_grid(a.config)
    if not grid:
        raise SystemExit(f"{a.config} has no 'sweep:' block")
    keys = sorted(grid)
    rows = []
    for combo in itertools.product(*(grid[k] for k in keys)):
        cell = cfg
        for k, v in zip(keys, combo):
            cell = set_path(cell, k, v)
        d = summarise_demand(run_demand(cell))
        rows.append({**dict(zip(keys, combo)), **d})
    t = pd.DataFrame(rows)
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "sweep_results.csv", index=False)
    print(f"{len(t)} cells -> {out/'sweep_results.csv'}\n")
    for k in keys:
        if k == "seed":
            continue
        g = t.groupby(k)["final_share_of_balances"].mean()
        lo, hi = g.min(), g.max()
        print(f"{k:<34} range {lo*100:6.2f}% - {hi*100:6.2f}%   leverage {hi/max(lo,1e-9):5.1f}x")
    return 0


def _cmd_verify(a):
    cfg = load_demand_config(a.config)
    x, y = run_demand(cfg), run_demand(cfg)
    ok = x.equals(y)
    print(f"config_hash: {content_hash(cfg)}")
    print(f"deterministic: {ok}")
    return 0 if ok else 1


def _cmd_aggregate(a):
    curves = {}
    for name, f in [("dm", "dm_developed"), ("em_mod", "em_moderate"),
                    ("em_high", "em_high_inflation")]:
        c = load_demand_config(f"configs/demand/{f}.yaml")
        runs = [run_demand(replace(c, seed=s))["adopted_share_of_balances"].values
                for s in (1, 2, 3)]
        curves[name] = np.mean(runs, axis=0)
    print(provenance_table(), "\n")
    for label, incl, grow in [("A accessible, static", False, False),
                              ("B accessible, grown", False, True),
                              ("C incl. restricted, grown", True, True)]:
        r = aggregate(curves, a.years, include_inaccessible=incl, grow_pools=grow)
        parts = "  ".join(f"{k} ${v:,.0f}bn" for k, v in r.items() if k != "TOTAL")
        print(f"{label:<28} TOTAL ${r['TOTAL']:,.0f}bn\n    {parts}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="genosim.demand_cli")
    s = p.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run"); r.add_argument("config"); r.add_argument("--outdir", default="results/demand"); r.add_argument("--seed", type=int); r.set_defaults(f=_cmd_run)
    w = s.add_parser("sweep"); w.add_argument("config"); w.add_argument("--outdir", default="results/demand_sweep"); w.set_defaults(f=_cmd_sweep)
    v = s.add_parser("verify"); v.add_argument("config"); v.set_defaults(f=_cmd_verify)
    g = s.add_parser("aggregate"); g.add_argument("--years", type=int, default=10); g.set_defaults(f=_cmd_aggregate)
    a = p.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    raise SystemExit(main())
