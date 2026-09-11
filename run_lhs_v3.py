# Copyright (c) 2026 Category One Limited (British Virgin Islands).
# All rights reserved. See LICENSE.
"""Global sensitivity analysis for demand model v3.

Every unmeasured parameter sampled simultaneously from a continuous range.
Cited parameters (inflation rates, current account penetration) held fixed.
"""
import sys
sys.path.insert(0, 'src')
from pathlib import Path
import numpy as np, pandas as pd
from genosim.demand_v3 import *

R = {
    "reach_external":         (0.01, 0.30),
    "reach_internal_within":  (0.10, 1.20),
    "reach_internal_across":  (0.02, 0.50),
    "trust_threshold_mean":   (0.003, 0.050),
    "salience_trust_effect":  (0.20, 0.90),
    "manufactured_salience":  (0.0,  0.50),
    "adoption_hazard":        (0.10, 0.90),
    "churn_base":             (0.01, 0.25),
    "alloc_initial":          (0.02, 0.20),
    "alloc_ramp_per_year":    (0.03, 0.30),
    "alloc_ceiling":          (0.25, 0.95),
    "account_growth":         (0.03, 0.30),
    "account_ceiling":        (0.35, 0.95),   # bank-rail vs exchange-rail
    "salience_halflife":      (3.0,  24.0),
    "salience_baseline":      (0.05, 0.50),
    "drawdown":               (0.05, 0.60),
    "roundtrip_spread":       (0.0025, 0.05),
}

MARKETS = {
 "dm": dict(local_inflation=0.03, median_balance=9000, pool=(0.93,0.02,0.05),
            phone=0.95, acct=0.27, sal=((0,0.45),), dsp=0.05, dss=0.30),
 "em_high": dict(local_inflation=0.30, median_balance=1500, pool=(0.55,0.30,0.15),
            phone=0.75, acct=0.256, sal=tuple((m,0.35) for m in range(0,120,12)), dsp=0.0, dss=0.0),
}

def main(chunk, nchunks, n_total, mkey):
    rng = np.random.default_rng(20260813 + chunk*17)
    spec = MARKETS[mkey]
    rows = []
    for _ in range(n_total // nchunks):
        p = {k: rng.uniform(lo, hi) for k, (lo, hi) in R.items()}
        if p["alloc_ceiling"] <= p["alloc_initial"]:
            p["alloc_ceiling"] = p["alloc_initial"] + 0.20
        mk = MarketConfigV3(name=mkey, households=25000,
            local_inflation=spec["local_inflation"], us_inflation=0.03,
            median_balance=spec["median_balance"],
            pool_local=spec["pool"][0], pool_stable=spec["pool"][1], pool_other=spec["pool"][2],
            annual_drawdown_fraction=p["drawdown"], smartphone_access=spec["phone"],
            account_penetration=spec["acct"], account_growth=p["account_growth"],
            account_ceiling=p["account_ceiling"],
            dollar_stress_prob=spec["dsp"], dollar_stress_severity=spec["dss"],
            salience_events=spec["sal"], salience_halflife_months=p["salience_halflife"],
            salience_baseline=p["salience_baseline"])
        pr = ProductConfigV3(roundtrip_spread=p["roundtrip_spread"])
        ad = AdoptionConfigV3(
            reach_external=p["reach_external"],
            reach_internal_within=p["reach_internal_within"],
            reach_internal_across=p["reach_internal_across"],
            trust_threshold_mean=p["trust_threshold_mean"],
            salience_trust_effect=p["salience_trust_effect"],
            manufactured_salience=p["manufactured_salience"],
            adoption_hazard=p["adoption_hazard"], churn_base=p["churn_base"],
            alloc_initial=p["alloc_initial"], alloc_ramp_per_year=p["alloc_ramp_per_year"],
            alloc_ceiling=p["alloc_ceiling"])
        cfg = DemandConfigV3(name='s', seed=int(rng.integers(1,10_000)),
                             market=mk, product=pr, adoption=ad)
        rows.append({**p, **summarise_demand_v3(run_demand_v3(cfg))})
    Path('results').mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(f'results/lhs_v3_{mkey}_{chunk}.csv', index=False)
    print(f'{mkey} chunk {chunk}: {len(rows)} samples')

if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
