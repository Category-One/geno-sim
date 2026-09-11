# Copyright (c) 2026 Category One Limited (British Virgin Islands).
# All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Demand model v2 — protection framing.

v1 is retained unchanged in demand.py. This is a separate model, not a
patch, because three structural assumptions changed:

  1. DIFFUSION is calibrated on M-Pesa rather than on stablecoin volume
     growth, and is split into REACH (people hear of it) and ACCESS (people
     can actually convert). M-Pesa reached 43% of Kenyan households in 17
     months and ~70% within four years, and every account of it attributes
     that to the agent network -- 4,000 to 19,000 cash-in/cash-out outlets
     against ~850 bank branches nationally -- not to advertising. Awareness
     without an on-ramp does nothing.

  2. ALLOCATION is no longer a function of gain magnitude. v1 indexed the
     allocated share to the size of the benefit, which is portfolio logic.
     For an instrument with no premium, no lockup and full redeemability,
     the rational allocation of savings is not limited by how large the
     benefit is -- it is limited by liquidity needs and by trust. The
     gain-indexed curve (alloc_low / alloc_high) is removed. It was the
     single largest driver of the v1 developed-market result and had no
     empirical basis whatever.

  3. TRUST is modulated by SALIENCE rather than fixed. Protection-motivated
     switching is fast when the threat is vivid and slow when it is not.
     Deposits moved to large banks within days during the March 2023 SVB
     episode with no yield differential at all. Inflation's problem is that
     it is a slow erosion nobody experiences as a discrete loss.

Two salience channels are modelled separately because the evidence on them
differs sharply:

  ENDOGENOUS -- actual inflation prints and currency shocks. Spikes and
    decays. Well evidenced: flood and earthquake insurance take-up rises
    after nearby events and decays over following years.

  MANUFACTURED -- campaign-driven. Persistent while funded, lower ceiling.
    NOT well evidenced for this product. Distant-catastrophe appeals
    ("your currency survived Venezuela") historically underperform. An
    appeal that makes an ALREADY-INCURRED loss legible ("here is what your
    savings did in 2022") is a different proposition with no clean
    reference class. Swept, never assumed.

On the zero-price point: Cohen and Dupas found bed-net take-up near 75% when
free, collapsing to ~20% at a small positive price -- a cliff at zero, not an
elasticity. That supports a LOW trust threshold for a no-premium product. It
does not support a zero threshold: a free bed net has no downside, whereas
moving savings into a novel instrument carries perceived principal risk. The
threshold stays, at a low level.

=============================================================================
Parameters marked  # >>> UNMEASURED  have no empirical basis and must be
swept, never reported as point estimates.
=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketConfigV2:
    """Market structure. Inflation figures are cited; pool splits are not."""

    name: str = "market"
    households: int = 100_000
    local_inflation: float = 0.30
    us_inflation: float = 0.03
    median_balance: float = 2_000.0
    balance_sigma: float = 1.2
    pool_local: float = 0.70
    pool_stable: float = 0.20
    pool_other: float = 0.10
    annual_drawdown_fraction: float = 0.12
    smartphone_access: float = 0.75

    # Dollar tail risk, as perceived by a USD-stablecoin holder.
    dollar_stress_prob: float = 0.0        # >>> UNMEASURED
    dollar_stress_severity: float = 0.0    # >>> UNMEASURED

    # --- endogenous salience ---
    # Months in which inflation becomes vivid: a high print, a currency
    # shock, an election fought on cost of living. Modelled as (month,
    # magnitude) with exponential decay. High-inflation markets have these
    # continuously; developed markets had one episode in 2021-23.
    salience_events: tuple[tuple[int, float], ...] = ()
    salience_halflife_months: float = 9.0   # >>> UNMEASURED
    salience_baseline: float = 0.15         # background awareness of erosion


@dataclass(frozen=True)
class ProductConfigV2:
    protection_rate: float = 1.0           # design assumption, taken as given
    roundtrip_spread: float = 0.01
    spread_floor: float = 0.002
    spread_halflife_access: float = 0.30
    redemption_fee: float = 0.07           # backstop path only


@dataclass(frozen=True)
class AdoptionConfigV2:
    """Diffusion, access, trust and salience."""

    # --- reach: people hear it exists ---
    reach_external: float = 0.10           # >>> UNMEASURED
    reach_internal: float = 0.40           # word of mouth  >>> UNMEASURED

    # --- access: people can actually convert ---
    # M-Pesa's binding constraint. An aware household with no on-ramp cannot
    # adopt regardless of how much it wants to. Access grows with investment
    # and with adoption (agents follow demand), toward a ceiling.
    access_initial: float = 0.05           # share of population with an on-ramp
    access_growth: float = 0.60            # annual growth in coverage
    access_ceiling: float = 0.95
    access_follows_adoption: float = 0.50  # agents open where demand exists

    # --- trust ---
    # Low, per the zero-price finding, but non-zero: perceived principal risk.
    trust_threshold_mean: float = 0.015    # >>> UNMEASURED
    trust_threshold_sd: float = 0.012
    # Salience multiplies the threshold DOWN: a vivid threat lowers the bar.
    salience_trust_effect: float = 0.60    # >>> UNMEASURED
    # Manufactured salience: campaign-driven, persistent while funded.
    manufactured_salience: float = 0.0     # >>> UNMEASURED — sweep, never assume
    validation_events: tuple[tuple[int, float], ...] = ()

    adoption_hazard: float = 0.40          # >>> UNMEASURED
    churn_base: float = 0.05               # >>> UNMEASURED

    # --- allocation ---
    # No longer indexed to gain. Bounded by liquidity need and by trust.
    # A household keeps a working buffer outside CIC; the rest can move.
    working_buffer_months: float = 3.0     # kept liquid, not in CIC
    trust_allocation_effect: float = 0.70  # how much trust gates allocation


@dataclass(frozen=True)
class DemandConfigV2:
    name: str
    seed: int
    n_steps: int = 120
    steps_per_year: int = 12
    market: MarketConfigV2 = field(default_factory=MarketConfigV2)
    product: ProductConfigV2 = field(default_factory=ProductConfigV2)
    adoption: AdoptionConfigV2 = field(default_factory=AdoptionConfigV2)
    notes: str = ""


# ---------------------------------------------------------------------------
# Economics
# ---------------------------------------------------------------------------

def marginal_gain(holding: np.ndarray, m: MarketConfigV2,
                  p: ProductConfigV2) -> np.ndarray:
    """Annual purchasing-power protection, by current holding.

    Unchanged from v1: this part was grounded. Local-currency holders gain
    local inflation; USD-stablecoin holders gain US inflation plus whatever
    dollar tail risk they perceive.
    """
    tail = m.dollar_stress_prob * m.dollar_stress_severity
    g = np.empty_like(holding, dtype=float)
    g[holding == 0] = m.local_inflation * p.protection_rate
    g[holding == 1] = (m.us_inflation + tail) * p.protection_rate
    g[holding == 2] = (m.us_inflation * 0.5 + tail) * p.protection_rate
    return g


def salience(t: int, m: MarketConfigV2, manufactured: float) -> float:
    """Combined salience in [0, 1] at month t.

    Endogenous events spike and decay; manufactured salience is flat while
    funded. Capped at 1.0 -- a campaign cannot make inflation more vivid
    than a currency collapse.
    """
    s = m.salience_baseline
    for month, mag in m.salience_events:
        if t >= month:
            s += mag * 0.5 ** ((t - month) / max(m.salience_halflife_months, 1e-9))
    return float(min(s + manufactured, 1.0))


def access_share(t: int, adopted_share: float, a: AdoptionConfigV2,
                 dt: float) -> float:
    """Share of the population with a usable on-ramp.

    The M-Pesa lesson: this, not awareness, was the binding constraint.
    Grows autonomously with investment and additionally where demand
    already exists, since agents open where there are customers.
    """
    base = a.access_ceiling - (a.access_ceiling - a.access_initial) * \
        np.exp(-a.access_growth * t * dt)
    pulled = a.access_follows_adoption * adopted_share
    return float(min(base + pulled, a.access_ceiling))


def effective_spread(access: float, p: ProductConfigV2) -> float:
    """Conversion cost falls as on-ramp density rises."""
    decay = 0.5 ** (access / max(p.spread_halflife_access, 1e-9))
    return p.spread_floor + (p.roundtrip_spread - p.spread_floor) * decay


def target_allocation(drawdown: np.ndarray, trust_ok: np.ndarray,
                      a: AdoptionConfigV2) -> np.ndarray:
    """Share of savings a household will hold in CIC.

    NOT a function of gain. A household keeps a working buffer liquid and
    can move the remainder. Trust gates how much of that remainder actually
    moves. This replaces v1's gain-indexed curve, which was invented and
    dominated the v1 developed-market result.
    """
    buffer = np.clip(drawdown * a.working_buffer_months / 12.0, 0.0, 0.9)
    movable = 1.0 - buffer
    gate = np.where(trust_ok, 1.0, 1.0 - a.trust_allocation_effect)
    return np.clip(movable * gate, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_demand_v2(cfg: DemandConfigV2) -> pd.DataFrame:
    """One run. Deterministic given (cfg, seed)."""
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
    has_access = rng.random(n)          # percentile position for on-ramp access
    gain = marginal_gain(holding, m, p)

    aware = np.zeros(n, dtype=bool)
    adopted = np.zeros(n, dtype=bool)
    alloc = np.zeros(n)
    rows = []

    for t in range(cfg.n_steps + 1):
        share = float((balance * alloc).sum() / balance.sum())
        acc = access_share(t, share, a, dt)
        sal = salience(t, m, a.manufactured_salience)
        spread = effective_spread(acc, p)

        # reach
        p_aware = (a.reach_external + a.reach_internal * share) * dt
        aware |= addressable & ~aware & (rng.random(n) < p_aware)

        # trust threshold: salience lowers it; validation events step it down
        decay = 1.0 - a.salience_trust_effect * sal
        for ev_month, ev_effect in a.validation_events:
            if t >= ev_month:
                decay *= (1.0 - ev_effect)
        threshold = threshold0 * max(decay, 0.0)

        # decision: needs awareness AND access AND net advantage over threshold
        net = gain - spread * drawdown
        can_reach = has_access < acc
        trust_ok = net > threshold
        eligible = aware & can_reach & trust_ok & ~adopted
        adopters = eligible & (rng.random(n) < a.adoption_hazard * dt * cfg.steps_per_year)
        adopted |= adopters

        tgt = target_allocation(drawdown, trust_ok, a)
        alloc = np.where(adopted, np.minimum(alloc + tgt * dt / 2.0, tgt), alloc)

        leaving = adopted & (rng.random(n) < a.churn_base * dt)
        adopted &= ~leaving
        alloc = np.where(leaving, 0.0, alloc)

        rows.append({
            "step": t, "year": t * dt,
            "adopted_share_of_balances": share,
            "adopted_share_of_households": float(adopted.mean()),
            "cic_balances_usd": float((balance * alloc).sum()),
            "aware_share": float(aware.mean()),
            "access_share": acc,
            "salience": sal,
            "effective_spread": spread,
            "mean_threshold": float(threshold.mean()),
            "from_local": int((adopted & (holding == 0)).sum()),
            "from_stable": int((adopted & (holding == 1)).sum()),
        })
    return pd.DataFrame(rows)


def summarise_demand_v2(df: pd.DataFrame) -> dict[str, Any]:
    f = df.iloc[-1]
    last = df["adopted_share_of_balances"].iloc[-12:]
    return {
        "final_share_of_balances": float(f["adopted_share_of_balances"]),
        "final_share_of_households": float(f["adopted_share_of_households"]),
        "final_balances_usd": float(f["cic_balances_usd"]),
        "peak_share": float(df["adopted_share_of_balances"].max()),
        "final_access": float(f["access_share"]),
        "final_aware": float(f["aware_share"]),
        "self_sustaining": bool(last.iloc[-1] - last.iloc[0] > 0.001),
        "final_from_local": int(f["from_local"]),
        "final_from_stable": int(f["from_stable"]),
    }
