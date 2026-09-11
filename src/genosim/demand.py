# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Retail demand model: CIC as a reserve/savings layer.

Architecture assumed (per design discussion):
  CIC is HELD, not spent. To spend, a household converts CIC -> USDT (or
  local currency) and spends that. So merchant acceptance is NOT required.
  What is required is a liquid CIC<->USDT market in each target country.

Central mechanic — the marginal-gain split:
  A household's incentive to adopt depends on what it holds NOW, not on
  where it lives.
    * Holding local currency  -> gain = local inflation  (can be ~30%/yr)
    * Holding USD stablecoin  -> gain = US inflation     (~3%/yr, everywhere)
  Geography sets the size of the local-currency pool; it does NOT change the
  incentive facing someone already in USDT. Collapsing these two pools is
  what produces double-counting in TAM-style projections.

Output is a FAILURE BOUNDARY, not a demand number: the region of parameter
space where adoption becomes self-sustaining versus where it stalls.

=============================================================================
STUBS: functions marked  # >>> REPLACE  encode assumptions that are not
measured. They are stated explicitly so they can be swept rather than
believed. The protection rate in particular is taken as given by design
assumption, not derived.
=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketConfig:
    """One country / market segment.

    pool_local / pool_stable / pool_other must sum to 1.0. They split
    household savings by CURRENT holding, which is the variable that sets
    the marginal gain from adopting CIC.
    """

    name: str = "high_inflation"
    households: int = 100_000
    local_inflation: float = 0.30          # annual, local CPI
    us_inflation: float = 0.03             # annual, USD erosion
    median_balance: float = 2_000.0        # in USD terms
    balance_sigma: float = 1.2             # lognormal shape
    pool_local: float = 0.70               # share of balances in local ccy
    pool_stable: float = 0.20              # share already in USD stablecoins
    pool_other: float = 0.10               # cash dollars, gold, etc.
    # Fraction of the savings balance withdrawn per year. Drives holding
    # cost: friction = roundtrip_spread x this. NOT a transaction count.
    #
    # DERIVED, not measured. Identity:
    #   drawdown_fraction = (share withdrawing p.a.) x (avg withdrawal / avg balance)
    # US anchors: Bankrate Feb 2025, 1,302 of 3,480 adults withdrew from
    # emergency savings in 12 months = 37%; modal withdrawal $1,000-2,499
    # (midpoint ~$1,750); median transaction-account balance ~$8,000.
    #   narrow  0.37 x (1750/8000) = 0.081
    #   broad   0.66 x (1750/8000) = 0.144   [LendingTree: 66% used savings]
    # DM set to 0.12 (between the two). EM set higher on greater income
    # volatility and thinner buffers -- that step is judgement, not data.
    # SWEEP 0.05-0.60.
    annual_drawdown_fraction: float = 0.12
    smartphone_access: float = 0.75        # ceiling on addressable population
    # --- dollar tail risk ---
    # A USD-stablecoin holder is exposed to dollar debasement/stress, not just
    # steady US CPI. This is the term that determines whether the USDT pool is
    # convertible at all: without it, their gain from CIC is only ~3%/yr.
    # Both values are UNMEASURED and must be swept, not assumed.
    dollar_stress_prob: float = 0.0        # annual probability of a stress event
    dollar_stress_severity: float = 0.0    # fractional purchasing-power loss if it occurs


@dataclass(frozen=True)
class ProductConfig:
    """CIC's terms as they face a retail household."""

    protection_rate: float = 1.0           # 1.0 = full protection (design assumption)
    roundtrip_spread: float = 0.01         # CIC<->USDT, both legs
    spread_floor: float = 0.002            # competition compresses toward this
    spread_halflife_share: float = 0.05    # adopted share at which spread halves
    acquisition_fee: float = 0.0           # one-off, on entry
    redemption_fee: float = 0.07           # backstop only; not on the spend path
    min_balance: float = 0.0


@dataclass(frozen=True)
class AdoptionConfig:
    """Diffusion, trust and churn."""

    awareness_external: float = 0.02       # marketing reach per period
    awareness_internal: float = 0.15       # word-of-mouth coefficient
    # Required excess return, in ABSOLUTE annual terms, to move savings into
    # an unfamiliar instrument from an unproven issuer. This is a risk
    # premium, not a multiple.
    #
    # CORRECTED. An earlier version computed the hurdle as
    # trust_threshold_mean x us_inflation (~1.05%), which sat far below the
    # ~3% developed-market gain, so every agent cleared it and the parameter
    # was inert. That also inflated awareness's apparent leverage, since
    # nothing else bound.
    #
    # As an absolute premium the parameter binds where it should: in
    # developed markets, where the ~3% gain is the same order of magnitude
    # as the premium demanded, and not in high-inflation markets, where a
    # 30% gain clears any plausible premium. UNMEASURED -- sweep it.
    trust_threshold_mean: float = 0.025    # 2.5%/yr required excess return
    trust_threshold_sd: float = 0.015
    trust_decay_per_year: float = 0.10     # threshold falls as track record builds
    # --- discrete validation events ---
    # Passive track-record drift (above) is the wrong shape for validation.
    # A published audit, a recurring reserve attestation, a named team, or a
    # recognised institution taking a position are STEP CHANGES in the trust
    # threshold, not drift. Each event multiplies the remaining threshold by
    # (1 - effect) from its month onward.
    #
    # Lead times are real and sequential: audit ~3-6 months to a published
    # report, attestation ~2-4 months to establish then recurring, and a
    # credible independent review of a proprietary mechanism 6-12 months.
    # Nothing here happens at month 0.
    #
    # UNMEASURED. Effect sizes are judgement. SWEEP them.
    validation_events: tuple[tuple[int, float], ...] = ()   # (month, effect)
    # --- launch campaign ---
    # Crypto launches now reach scale in weeks, not years. Ethena's USDe
    # went from launch (19 Feb 2024) to $1bn supply on 13 Mar 2024 -- 23
    # days -- and $2bn in seven weeks, driven by ~19% sUSDe yield plus a
    # points/airdrop programme that drew 41k users.
    #
    # That is CRYPTO CAPITAL ROTATING, not household savings converting.
    # Modelled separately from organic diffusion so the two contributions
    # can be read apart: the burst has a crypto-native precedent, the
    # organic curve has household evidence. Do not let one launder the other.
    launch_awareness_multiple: float = 1.0   # 1.0 = no campaign
    launch_halflife_months: float = 6.0      # decay of the campaign effect
    launch_reaches_crypto_only: bool = True  # burst hits pool_stable/other first
    churn_base: float = 0.05               # annual, unrelated to performance
    # Rate at which an aware, willing household actually acts. Previously
    # hardcoded at 0.25/yr inside the loop, which hid it from every sweep.
    adoption_hazard: float = 0.25
    # Allocation-curve anchors: share of savings allocated at low gain (~3%)
    # and high gain (~30%). The "3.75x asymmetry" reported earlier was simply
    # alloc_high / alloc_low -- an input, not a finding. Swept here.
    alloc_low: float = 0.20
    alloc_high: float = 0.75
    churn_on_liquidity_fail: float = 0.60  # leave if a conversion fails
    liquidity_depth_per_adopter: float = 0.4   # market depth scales with adoption
    liquidity_fail_threshold: float = 0.5  # depth below this -> failed conversions


@dataclass(frozen=True)
class DemandConfig:
    name: str
    seed: int
    n_steps: int = 120                     # months
    steps_per_year: int = 12
    market: MarketConfig = field(default_factory=MarketConfig)
    product: ProductConfig = field(default_factory=ProductConfig)
    adoption: AdoptionConfig = field(default_factory=AdoptionConfig)
    notes: str = ""


# ---------------------------------------------------------------------------
# Core economics
# ---------------------------------------------------------------------------

def marginal_gain(holding: np.ndarray, market: MarketConfig,
                  product: ProductConfig) -> np.ndarray:
    """Annual real gain from moving to CIC, by CURRENT holding.

    holding: 0 = local currency, 1 = USD stablecoin, 2 = other store of value

    This is the model's central asymmetry. Someone in pesos gains local
    inflation. Someone already in USDT gains only US inflation — the same
    ~3% whether they are in Buenos Aires or London.

    # >>> REPLACE if CIC's protection is partial rather than complete, or if
    # >>> it is defined against a basket that differs from local CPI.
    """
    # Expected annual loss from a dollar stress event. This is what makes the
    # USD-stablecoin pool addressable at all. A holder who assigns, say, 8%
    # annual probability to a 30% purchasing-power event carries 2.4%/yr of
    # expected loss -- roughly doubling their gain from switching.
    tail = market.dollar_stress_prob * market.dollar_stress_severity

    gain = np.empty_like(holding, dtype=float)
    # Local-currency holders face local inflation AND, in most target markets,
    # their own currency's tail risk, which dwarfs the dollar's.
    gain[holding == 0] = market.local_inflation * product.protection_rate
    # USD-stablecoin holders: steady US CPI plus dollar tail risk.
    gain[holding == 1] = (market.us_inflation + tail) * product.protection_rate
    gain[holding == 2] = (market.us_inflation * 0.5 + tail) * product.protection_rate
    return gain


def target_allocation(gain: np.ndarray, alloc_low: float = 0.20,
                      alloc_high: float = 0.75,
                      gain_low: float = 0.03, gain_high: float = 0.30) -> np.ndarray:
    """Fraction of savings a household allocates to CIC.

    Households allocate a SHARE rather than switching all-or-nothing.

    NO EXTERNAL SATURATION ANCHOR IS USED. Earlier versions imported the
    TIPS share of Treasury debt (~7.5%) as the low-gain anchor. That was a
    category error: TIPS competes for money already allocated to government
    bonds by investors who hold equities, property and other real assets, so
    a small dedicated sleeve is rational for them. The relevant population
    here holds cash savings with no protection from any source, so their
    counterfactual exposure is 100%, not 7%.

    Because no instrument with CIC's properties has existed for this
    population, the saturation level is UNMEASURED. It is therefore a swept
    parameter, not a calibrated constant. What the model can say without it:
    at realistic diffusion speeds a 10-year horizon reaches only a modest
    fraction of whatever the plateau turns out to be, so the near-term
    trajectory is rate-limited rather than ceiling-limited.

    Defaults below are placeholders in the middle of a plausible range.

    # >>> SWEEP alloc_low and alloc_high. Do not report a single value.
    """
    g = np.clip(gain, 1e-6, None)
    lo, hi = np.log(gain_low), np.log(gain_high)
    frac = np.clip((np.log(g) - lo) / (hi - lo), 0.0, 1.0)
    return alloc_low + (alloc_high - alloc_low) * frac


def effective_spread(adopted_share: float, product: ProductConfig) -> float:
    """Conversion cost, declining as market depth builds.

    Exchange competition compresses spreads with volume. Modelled as
    exponential decay from the launch spread toward a competitive floor.
    """
    if adopted_share <= 0:
        return product.roundtrip_spread
    decay = 0.5 ** (adopted_share / max(product.spread_halflife_share, 1e-9))
    return product.spread_floor + (product.roundtrip_spread - product.spread_floor) * decay


def annual_friction(spread: float, drawdown_fraction: np.ndarray,
                    product: ProductConfig) -> np.ndarray:
    """Annualised holding cost, as a fraction of the CIC balance.

    CORRECTED. An earlier version computed `spread * spend_events`, treating
    CIC as the SPENDING balance and producing an absurd ~18%/yr drag. That is
    wrong for this architecture. CIC is the SAVINGS layer: households spend
    from income and current balances, and touch CIC only when they draw down
    savings.

    The round trip is paid on the PORTION WITHDRAWN, not on the whole
    balance. A household holding 1,000 that withdraws 200 pays the spread on
    200; the remaining 800 sits untouched. So annual cost as a fraction of
    the balance is:

        spread x (fraction of balance withdrawn per year)

    At a 1% round trip and 30% annual drawdown, that is 0.3%/yr -- an order
    of magnitude below the earlier treatment. The cost does not accumulate
    per transaction unless the same capital is cycled repeatedly, which is
    trading behaviour rather than saving behaviour.

    # >>> REPLACE if entry and exit spreads differ, or if there is a fee
    # >>> structure beyond a symmetric round trip.
    """
    return spread * np.clip(drawdown_fraction, 0.0, 1.0) + product.acquisition_fee


def net_advantage(holding: np.ndarray, drawdown: np.ndarray,
                  adopted_share: float, market: MarketConfig,
                  product: ProductConfig) -> np.ndarray:
    """Annual advantage of CIC over the household's current holding, net of cost."""
    spread = effective_spread(adopted_share, product)
    return marginal_gain(holding, market, product) - annual_friction(
        spread, drawdown, product
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_demand(cfg: DemandConfig) -> pd.DataFrame:
    """Agent-based adoption run. Deterministic given (cfg, seed)."""
    rng = np.random.default_rng(cfg.seed)
    m, p, a = cfg.market, cfg.product, cfg.adoption
    n = m.households
    dt = 1.0 / cfg.steps_per_year

    # --- population, drawn once, in fixed order ---
    balance = rng.lognormal(np.log(m.median_balance), m.balance_sigma, n)
    holding = rng.choice(
        [0, 1, 2], size=n, p=[m.pool_local, m.pool_stable, m.pool_other]
    )
    # Heterogeneous drawdown behaviour, centred on the market mean and
    # bounded to [0, 1]: nobody withdraws more than their balance per year.
    drawdown = np.clip(rng.gamma(2.0, m.annual_drawdown_fraction / 2.0, n), 0.0, 1.0)
    threshold = np.clip(
        rng.normal(a.trust_threshold_mean, a.trust_threshold_sd, n), 0.0, None
    )
    addressable = rng.random(n) < m.smartphone_access

    aware = np.zeros(n, dtype=bool)
    adopted = np.zeros(n, dtype=bool)
    ever_adopted = np.zeros(n, dtype=bool)
    # Partial allocation: each household's TARGET share of savings in CIC,
    # anchored on TIPS (low gain) and stablecoin (high gain) data.
    gain_vec = marginal_gain(holding, m, p)
    alloc_target = target_allocation(gain_vec, a.alloc_low, a.alloc_high)
    alloc = np.zeros(n)          # current allocated fraction

    rows = []
    for t in range(cfg.n_steps + 1):
        share = float((balance * alloc).sum() / balance.sum())

        # --- awareness diffusion (Bass): external reach + word of mouth ---
        # Launch campaign multiplies external reach, decaying exponentially.
        campaign = 1.0
        if a.launch_awareness_multiple > 1.0:
            campaign = 1.0 + (a.launch_awareness_multiple - 1.0) * \
                0.5 ** (t / max(a.launch_halflife_months, 1e-9))
        ext = a.awareness_external * campaign
        p_aware = (ext + a.awareness_internal * share) * dt
        draw = rng.random(n)
        if a.launch_reaches_crypto_only and campaign > 1.0:
            # A points/airdrop campaign reaches people already on-chain.
            # Households not in crypto see only the baseline external rate.
            base_p = (a.awareness_external + a.awareness_internal * share) * dt
            p_vec = np.where(holding != 0, p_aware, base_p)
        else:
            p_vec = np.full(n, p_aware)
        newly = addressable & ~aware & (draw < p_vec)
        aware |= newly

        # --- liquidity: depth scales with adoption; thin markets fail ---
        depth = share / max(a.liquidity_depth_per_adopter, 1e-9)
        liquidity_ok = depth >= a.liquidity_fail_threshold or share == 0.0

        # --- trust threshold: passive drift plus discrete validation ---
        decay = (1.0 - a.trust_decay_per_year) ** (t * dt)
        for ev_month, ev_effect in a.validation_events:
            if t >= ev_month:
                decay *= (1.0 - ev_effect)
        current_threshold = threshold * decay

        # --- adoption decision ---
        adv = net_advantage(holding, drawdown, share, m, p)
        wants = adv > current_threshold
        eligible = aware & ~adopted & wants & (balance >= p.min_balance)
        adopters = eligible & (rng.random(n) < a.adoption_hazard * dt * cfg.steps_per_year)
        adopted |= adopters
        ever_adopted |= adopters
        # allocation ramps toward target over ~2 years once adopted
        alloc = np.where(adopted, np.minimum(alloc + alloc_target * dt / 2.0,
                                             alloc_target), alloc)

        # --- churn ---
        churn_rate = a.churn_base * dt
        if not liquidity_ok and share > 0:
            churn_rate += a.churn_on_liquidity_fail * dt
        leaving = adopted & (rng.random(n) < churn_rate)
        adopted &= ~leaving
        alloc = np.where(leaving, 0.0, alloc)

        rows.append({
            "step": t,
            "year": t * dt,
            "adopted_count": int(adopted.sum()),
            "adopted_share_of_households": float(adopted.sum() / n),
            "adopted_share_of_balances": share,
            "cic_balances_usd": float((balance * alloc).sum()),
            "mean_alloc_of_adopters": float(alloc[adopted].mean()) if adopted.any() else 0.0,
            "aware_share": float(aware.sum() / n),
            "effective_spread": effective_spread(share, p),
            "liquidity_ok": liquidity_ok,
            "from_local": int((adopted & (holding == 0)).sum()),
            "from_stable": int((adopted & (holding == 1)).sum()),
            "from_other": int((adopted & (holding == 2)).sum()),
            "churned_ever": int((ever_adopted & ~adopted).sum()),
        })

    return pd.DataFrame(rows)


def summarise_demand(df: pd.DataFrame) -> dict[str, Any]:
    """Metrics that decide whether adoption is self-sustaining."""
    final = df.iloc[-1]
    peak = df["adopted_share_of_balances"].max()
    last_year = df.iloc[-12:]["adopted_share_of_balances"]
    trend = float(last_year.iloc[-1] - last_year.iloc[0])
    return {
        "final_share_of_balances": float(final["adopted_share_of_balances"]),
        "final_share_of_households": float(final["adopted_share_of_households"]),
        "final_balances_usd": float(final["cic_balances_usd"]),
        "peak_share": float(peak),
        "stalled": bool(peak > 0 and final["adopted_share_of_balances"] < 0.5 * peak),
        "self_sustaining": bool(trend > 0.001),
        "final_from_local": int(final["from_local"]),
        "final_from_stable": int(final["from_stable"]),
        "churned_ever": int(final["churned_ever"]),
        "final_spread": float(final["effective_spread"]),
    }
