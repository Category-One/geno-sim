# Copyright (c) 2026 Category One Limited (British Virgin Islands).
# All rights reserved. See LICENSE.
"""Print the v3 ten-year projection and market breakdown."""
import sys; sys.path.insert(0, 'src')
import numpy as np
from genosim.demand_v3 import *
from genosim.pools import POOLS

DM = MarketConfigV3(name='dm', local_inflation=0.03, us_inflation=0.03, median_balance=9000,
   pool_local=0.93, pool_stable=0.02, pool_other=0.05, annual_drawdown_fraction=0.12,
   smartphone_access=0.95, account_penetration=0.27, account_growth=0.10, account_ceiling=0.70,
   salience_events=((0,0.45),), salience_baseline=0.15,
   dollar_stress_prob=0.05, dollar_stress_severity=0.30)
EMM = MarketConfigV3(name='emm', local_inflation=0.06, us_inflation=0.03, median_balance=2500,
   pool_local=0.85, pool_stable=0.08, pool_other=0.07, annual_drawdown_fraction=0.20,
   smartphone_access=0.80, account_penetration=0.21, account_growth=0.14, account_ceiling=0.72,
   salience_events=((0,0.30),(48,0.25)), salience_baseline=0.20)
EMH = MarketConfigV3(name='emh', local_inflation=0.30, us_inflation=0.03, median_balance=1500,
   pool_local=0.55, pool_stable=0.30, pool_other=0.15, annual_drawdown_fraction=0.30,
   smartphone_access=0.75, account_penetration=0.256, account_growth=0.15, account_ceiling=0.75,
   salience_events=tuple((m,0.35) for m in range(0,120,12)), salience_baseline=0.30)

cv = {}
for k, mk in (('dm', DM), ('em_mod', EMM), ('em_high', EMH)):
    cv[k] = np.mean([run_demand_v3(DemandConfigV3(name='x', seed=s, market=mk))
                     ['adopted_share_of_balances'].values for s in (1, 2, 3)], axis=0)

def agg(y, incl, grow):
    tot, parts = 0.0, {}
    for p in POOLS:
        if not p.accessible and not incl:
            continue
        v = p.value_usd_tn * ((1 + p.annual_growth) ** y if grow else 1.0)
        c = v * cv[p.curve][y * 12] * 1000
        parts[p.name] = c; tot += c
    return tot, parts

print("\nCIC held balances, $bn  (model v3)\n")
print(f"{'Yr':>3}{'A: static pools':>17}{'B: grown':>12}{'C: incl. restricted':>21}")
for y in range(1, 11):
    print(f"{y:>3}{agg(y,False,False)[0]:>16,.0f}{agg(y,False,True)[0]:>12,.0f}"
          f"{agg(y,True,True)[0]:>21,.0f}")
b10, parts = agg(10, False, True)
print("\nYear-10 scenario B, by pool:")
for k, v in sorted(parts.items(), key=lambda x: -x[1]):
    print(f"   {k:<46}{v:>9,.0f}bn ({v/b10*100:4.1f}%)")
print("\nYear-10 adoption share of household savings balances:")
for k in cv:
    print(f"   {k:<10}{cv[k][120]*100:6.2f}%")
print("\nCONDITIONS: mechanism assumed to deliver as specified; scenario C")
print("includes markets excluded elsewhere on capital controls. Read")
print("ASSUMPTIONS.md before citing any figure.\n")
