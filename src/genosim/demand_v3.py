# Copyright (c) 2026 Category One Limited (British Virgin Islands).
# All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Demand model v3 — access-constrained, experience-ramped.

v1 (demand.py) and v2 (demand_v2.py) are retained unchanged. This is a third
model, not a patch. Three structural changes from v2, each replacing an
invented parameter with a cited one or with a mechanism that encodes an
argued position.

  1. ACCESS is exchange-account penetration, not a smartphone ceiling or an
     invented build rate. Day-one reach is the population that already holds
     a crypto account, because DEX liquidity plus in-app MPC wallets (Binance
     Web3 Wallet and equivalents) make purchase a two-tap operation for that
     group with no listing decision required. Everyone else must first open
     an account and pass KYC.

     CITED (2026): US ~30% of adults; UK ~24%; Turkey ~25.6% of internet
     population; Brazil ~20.6%; South Africa ~19.6%; Philippines ~22-23%;
     global ~21% of internet-connected adults, ~9.9% of world population.
     Steep age gradient: male ownership ~16.2% at 25-34, ~3.2% at 65+.

  2. DIFFUSION is two-population. Word of mouth is fast WITHIN the
     account-holding population, because the listener can act immediately.
     It is slow ACROSS to non-holders, because acting requires opening an
     account first. At ~25% penetration the speaking population is not
     insular -- most households know several account holders -- so the
     crossing rate is low but not negligible.

  3. ALLOCATION ramps with EXPERIENCE, not with time or gain. A household
     starts small, holds, observes that it works, and increases. This
     encodes the position that conviction is earned rather than assumed,
     and it has a testable implication: mean allocation across adopters
     should sit well below the ceiling for as long as adoption is growing,
     because recent joiners drag the average down.

     v2 allowed adopters to reach ~97% of savings within two years, bounded
     only by a three-month working buffer. That produced a 63% developed-
     market share which is not defensible as a near-term figure. The ceiling
     may still be reached eventually; the ramp is what was missing.

=============================================================================
Parameters marked  # >>> UNMEASURED  have no empirical basis. Sweep them.
Parameters marked  # >>> CITED       trace to a published figure.
=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MarketConfigV3:
    name: str = "market"
    households: int = 100_000
    local_inflation: float = 0.30          # >>> CITED national CPI
    us_inflation: float = 0.03             # >>> CITED
    median_balance: float = 2_000.0
    balance_sigma: float = 1.2
    pool_local: float = 0.70
    pool_stable: float = 0.20
    pool_other: float = 0.10
    annual_drawdown_fraction: float = 0.12
    smartphone_access: float = 0.85

    # --- access: exchange-account penetration ---
    account_penetration: float = 0.25      # >>> CITED, per market
    account_growth: float = 0.12           # >>> UNMEASURED annual growth
    account_ceiling: float = 0.70          # >>> UNMEASURED

    dollar_stress_prob: float = 0.0        # >>> UNMEASURED
    dollar_stress_severity: float = 0.0    # >>> UNMEASURED

    salience_events: tuple[tuple[int, float], ...] = ()
    salience_halflife_months: float = 9.0  # >>> UNMEASURED
    salience_baseline: float = 0.15        # >>> UNMEASURED


@dataclass(frozen=True)
class ProductConfigV3:
    protection_rate: float = 1.0           # design assumption, taken as given
    roundtrip_spread: float = 0.01
    spread_floor: float = 0.002
    redemption_fee: float = 0.07


@dataclass(frozen=True)
class AdoptionConfigV3:
    # --- two-population diffusion ---
    reach_external: float = 0.10           # >>> UNMEASURED marketing reach
    reach_internal_within: float = 0.60    # >>> UNMEASURED WoM among holders
    reach_internal_across: float = 0.15    # >>> UNMEASURED WoM to non-holders

    # --- trust ---
    trust_threshold_mean: float = 0.015    # >>> UNMEASURED
    trust_threshold_sd: float = 0.012
    salience_trust_effect: float = 0.60    # >>> UNMEASURED
    manufactured_salience: float = 0.0     # >>> UNMEASURED
    validation_events: tuple[tuple[int, float], ...] = ()

    adoption_hazard: float = 0.40          # >>> UNMEASURED
    churn_base: float = 0.05               # >>> UNMEASURED

    # --- experience-based allocation ramp ---
    # Conviction is earned. A household commits a small share first and
    # increases only after holding successfully.
    alloc_initial: float = 0.05            # >>> UNMEASURED share on first adoption
    alloc_ramp_per_year: float = 0.12      # >>> UNMEASURED increase per year held
    alloc_ceiling: float = 0.60            # >>> UNMEASURED long-run maximum
    working_buffer_months: float = 3.0     # kept liquid regardless


@dataclass(frozen=True)
class DemandConfigV3:
    name: str
    seed: int
    n_steps: int = 120
    steps_per_year: int = 12
    market: MarketConfigV3 = field(default_factory=MarketConfigV3)
    product: ProductConfigV3 = field(default_factory=ProductConfigV3)
    adoption: AdoptionConfigV3 = field(default_factory=AdoptionConfigV3)
    notes: str = ""


# ---------------------------------------------------------------------------

def marginal_gain(holding: np.ndarray, m: MarketConfigV3,
                  p: ProductConfigV3) -> np.ndarray:
    """Annual purchasing-power protection by current holding. Grounded."""
    tail = m.dollar_stress_prob * m.dollar_stress_severity
    g = np.empty_like(holding, dtype=float)
    g[holding == 0] = m.local_inflation * p.protection_rate
    g[holding == 1] = (m.us_inflation + tail) * p.protection_rate
    g[holding == 2] = (m.us_inflation * 0.5 + tail) * p.protection_rate
    return g


def salience(t: int, m: MarketConfigV3, manufactured: float) -> float:
    s = m.salience_baseline
    for month, mag in m.salience_events:
        if t >= month:
            s += mag * 0.5 ** ((t - month) / max(m.salience_halflife_months, 1e-9))
    return float(min(s + manufactured, 1.0))


def account_share(t: int, m: MarketConfigV3, dt: float) -> float:
    """Share of the population holding an exchange account at month t.

    This is the day-one access ceiling. Non-holders must open an account and
    pass KYC before they can act, which is modelled as a separate, slower
    diffusion channel rather than as an absolute barrier.
    """
    grown = m.account_penetration * (1.0 + m.account_growth) ** (t * dt)
    return float(min(grown, m.account_ceiling))


def experience_allocation(months_held: np.ndarray, drawdown: np.ndarray,
                          a: AdoptionConfigV3) -> np.ndarray:
    """Allocated share of savings, rising with time successfully held.

    Starts at alloc_initial, rises by alloc_ramp_per_year for each year held,
    capped at alloc_ceiling and further capped by the liquid working buffer.
    A household adopting in year 8 is still near its starting allocation at
    year 10 -- which is what keeps terminal figures modest while adoption is
    still spreading.
    """
    years = months_held / 12.0
    raw = a.alloc_initial + a.alloc_ramp_per_year * years
    buffer = np.clip(drawdown * a.working_buffer_months / 12.0, 0.0, 0.9)
    return np.clip(np.minimum(raw, a.alloc_ceiling), 0.0, 1.0 - buffer)


# ---------------------------------------------------------------------------

def run_demand_v3(cfg: DemandConfigV3) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    m, p, a = cfg.market, cfg.product, cfg.adoption
    n, dt = m.households, 1.0 / cfg.steps_per_year

    balance = rng.lognormal(np.log(m.median_balance), m.balance_sigma, n)
    holding = rng.choice([0, 1, 2], size=n,
                         p=[m.pool_local, m.pool_stable, m.pool_other])
    drawdown = np.clip(rng.gamma(2.0, m.annual_drawdown_fraction / 2.0, n), 0.0, 1.0)
    threshold0 = np.clip(rng.normal(a.trust_threshold_mean,
                                    a.trust_threshold_sd, n), 0.0, None)
    addressable = rng.random(n) < m.smartphone_access
    account_rank = rng.random(n)     # percentile position for account holding
    gain = marginal_gain(holding, m, p)

    aware = np.zeros(n, dtype=bool)
    adopted = np.zeros(n, dtype=bool)
    months_held = np.zeros(n)
    alloc = np.zeros(n)
    rows = []

    for t in range(cfg.n_steps + 1):
        share = float((balance * alloc).sum() / balance.sum())
        acct = account_share(t, m, dt)
        has_account = account_rank < acct
        sal = salience(t, m, a.manufactured_salience)
        spread = p.spread_floor + (p.roundtrip_spread - p.spread_floor) * \
            0.5 ** (share / 0.05)

        # two-population reach: fast among account holders, slow across
        adopted_holders = float((adopted & has_account).mean())
        p_within = (a.reach_external + a.reach_internal_within * adopted_holders) * dt
        p_across = (a.reach_external * 0.5 + a.reach_internal_across * share) * dt
        p_vec = np.where(has_account, p_within, p_across)
        aware |= addressable & ~aware & (rng.random(n) < p_vec)

        decay = 1.0 - a.salience_trust_effect * sal
        for ev_month, ev_effect in a.validation_events:
            if t >= ev_month:
                decay *= (1.0 - ev_effect)
        threshold = threshold0 * max(decay, 0.0)

        net = gain - spread * drawdown
        eligible = aware & has_account & (net > threshold) & ~adopted
        adopters = eligible & (rng.random(n) < a.adoption_hazard * dt * cfg.steps_per_year)
        adopted |= adopters

        months_held = np.where(adopted, months_held + 1.0, 0.0)
        alloc = np.where(adopted, experience_allocation(months_held, drawdown, a), 0.0)

        leaving = adopted & (rng.random(n) < a.churn_base * dt)
        adopted &= ~leaving
        months_held = np.where(leaving, 0.0, months_held)
        alloc = np.where(leaving, 0.0, alloc)

        rows.append({
            "step": t, "year": t * dt,
            "adopted_share_of_balances": share,
            "adopted_share_of_households": float(adopted.mean()),
            "cic_balances_usd": float((balance * alloc).sum()),
            "aware_share": float(aware.mean()),
            "account_share": acct,
            "salience": sal,
            "mean_alloc_of_adopters": float(alloc[adopted].mean()) if adopted.any() else 0.0,
            "mean_months_held": float(months_held[adopted].mean()) if adopted.any() else 0.0,
            "effective_spread": spread,
            "from_local": int((adopted & (holding == 0)).sum()),
            "from_stable": int((adopted & (holding == 1)).sum()),
        })
    return pd.DataFrame(rows)


def summarise_demand_v3(df: pd.DataFrame) -> dict[str, Any]:
    f = df.iloc[-1]
    last = df["adopted_share_of_balances"].iloc[-12:]
    return {
        "final_share_of_balances": float(f["adopted_share_of_balances"]),
        "final_share_of_households": float(f["adopted_share_of_households"]),
        "final_balances_usd": float(f["cic_balances_usd"]),
        "final_mean_alloc": float(f["mean_alloc_of_adopters"]),
        "final_account_share": float(f["account_share"]),
        "final_aware": float(f["aware_share"]),
        "peak_share": float(df["adopted_share_of_balances"].max()),
        "self_sustaining": bool(last.iloc[-1] - last.iloc[0] > 0.001),
        "final_from_local": int(f["from_local"]),
        "final_from_stable": int(f["from_stable"]),
    }
