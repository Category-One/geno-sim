"""Global sensitivity analysis by random sampling of the joint parameter space.

Full factorial over 11 parameters is 262,440 cells. Random sampling gives
better coverage per unit compute in high dimensions and supports proper
variance-based sensitivity rather than one-at-a-time comparison.

Every UNMEASURED behavioural parameter is sampled simultaneously from a
continuous range. Nothing behavioural is held fixed.
"""
import sys, json
sys.path.insert(0, 'src')
from pathlib import Path
from dataclasses import replace
import numpy as np, pandas as pd
from genosim.demand import run_demand, summarise_demand
from genosim.demand_config import load_demand_config

RANGES = {
    "awareness_external":        (0.005, 0.20),
    "awareness_internal":        (0.10,  1.00),
    "adoption_hazard":           (0.08,  0.80),
    "churn_base":                (0.01,  0.30),
    "trust_threshold_mean":      (0.005, 0.070),
    "alloc_low":                 (0.05,  0.40),
    "alloc_high":                (0.50,  0.95),
    "launch_awareness_multiple": (1.0,   20.0),
    "liquidity_depth_per_adopter":(0.10, 1.00),
    "roundtrip_spread":          (0.0025,0.05),
    "annual_drawdown_fraction":  (0.05,  0.80),
    "dollar_stress_prob":        (0.0,   0.15),
    "balance_sigma":             (0.8,   1.8),
}

def main(chunk, nchunks, n_total, market):
    rng = np.random.default_rng(20260813 + chunk)
    base = load_demand_config(f'configs/demand/{market}.yaml')
    base = replace(base, market=replace(base.market, households=25000))
    n = n_total // nchunks
    rows = []
    for _ in range(n):
        p = {k: rng.uniform(lo, hi) for k, (lo, hi) in RANGES.items()}
        if p["alloc_high"] <= p["alloc_low"]:
            p["alloc_high"] = p["alloc_low"] + 0.10
        c = replace(base,
            seed=int(rng.integers(1, 10_000)),
            market=replace(base.market,
                annual_drawdown_fraction=p["annual_drawdown_fraction"],
                dollar_stress_prob=p["dollar_stress_prob"],
                dollar_stress_severity=0.35,
                balance_sigma=p["balance_sigma"]),
            product=replace(base.product, roundtrip_spread=p["roundtrip_spread"]),
            adoption=replace(base.adoption,
                awareness_external=p["awareness_external"],
                awareness_internal=p["awareness_internal"],
                adoption_hazard=p["adoption_hazard"],
                churn_base=p["churn_base"],
                trust_threshold_mean=p["trust_threshold_mean"],
                alloc_low=p["alloc_low"], alloc_high=p["alloc_high"],
                launch_awareness_multiple=p["launch_awareness_multiple"],
                liquidity_depth_per_adopter=p["liquidity_depth_per_adopter"]))
        d = summarise_demand(run_demand(c))
        rows.append({**p, **d})
    Path('results').mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(f'results/lhs_{market}_{chunk}.csv', index=False)
    print(f'chunk {chunk}: {len(rows)} samples')

if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
