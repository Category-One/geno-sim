# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Deterministic simulation engine.

Determinism rules enforced here:
  * one Generator, created from the config seed, threaded explicitly
  * no module-level np.random calls anywhere in the package
  * no wall-clock time, no environment lookups inside the loop
  * raw time series written to disk; all analysis happens downstream
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RunConfig
from .model import (
    State,
    backing_ratio,
    cic_supply_delta,
    fee_flows,
    geno_delta,
    measure_velocity,
    observe_m_fiat,
    price_update,
    settle_redemptions,
)


def _fiat_path(cfg: RunConfig, rng: np.random.Generator) -> np.ndarray:
    """True M_fiat series. The oracle sees a lagged, noisy view of this."""
    sc = cfg.scenario
    dt = 1.0 / sc.steps_per_year
    rates = np.full(sc.n_steps + 1, sc.fiat_expansion_rate)
    if sc.fiat_shock_step is not None:
        rates[sc.fiat_shock_step:] += sc.fiat_shock_magnitude
    path = np.empty(sc.n_steps + 1)
    path[0] = 1.0
    for t in range(1, sc.n_steps + 1):
        path[t] = path[t - 1] * (1.0 + rates[t] * dt)
    return path


def _demand_path(cfg: RunConfig, rng: np.random.Generator) -> np.ndarray:
    """Exogenous demand for CIC. Replace with your demand model if you have one."""
    sc = cfg.scenario
    base = cfg.reserve.initial_claims
    noise = rng.normal(1.0, 0.02, sc.n_steps + 1)
    demand = base * noise
    if sc.demand_shock_step is not None:
        demand[sc.demand_shock_step:] *= 1.0 + sc.demand_shock_magnitude
    return demand


def _basket_returns(cfg: RunConfig, rng: np.random.Generator) -> np.ndarray:
    """Weighted portfolio return per step for the reserve basket."""
    sc = cfg.scenario
    res = cfg.reserve
    dt = 1.0 / sc.steps_per_year
    total = np.zeros(sc.n_steps + 1)
    for key, weight in res.basket_weights.items():
        vol = res.basket_vol[key]
        drift = res.basket_drift[key]
        shocks = rng.normal(
            drift * dt, vol * np.sqrt(dt), sc.n_steps + 1
        )
        total += weight * shocks
    return total


def run(cfg: RunConfig) -> pd.DataFrame:
    """Execute one run. Returns the raw time series, unaggregated."""
    rng = np.random.default_rng(cfg.seed)
    sc, mech, res = cfg.scenario, cfg.mechanism, cfg.reserve

    # Draw all exogenous paths up front, in fixed order. This keeps the RNG
    # consumption independent of branching inside the loop, so changing a
    # threshold does not silently reshuffle every random draw.
    m_fiat_true = _fiat_path(cfg, rng)
    demand = _demand_path(cfg, rng)
    basket_ret = _basket_returns(cfg, rng)
    volume_noise = rng.normal(1.0, 0.1, sc.n_steps + 1)

    state = State(
        step=0,
        cic_supply=res.initial_claims,
        geno_supply=res.initial_claims * 0.1,
        reserve_value=res.initial_reserve_value + res.external_capital,
        claims_outstanding=res.initial_claims,
        m_fiat=m_fiat_true[0],
        velocity=1.0,
        price=res.redemption_ratio,
        pending_redemptions=0.0,
        redemption_queue=[],
    )

    volume_history = np.zeros(sc.n_steps + 1)
    rows = []
    prev_observed = observe_m_fiat(
        m_fiat_true, 0, sc.oracle_lag, 0.0, rng
    )

    for t in range(sc.n_steps + 1):
        state.step = t
        state.m_fiat = m_fiat_true[t]

        # --- reserve assets revalue ---
        state.reserve_value *= 1.0 + basket_ret[t]

        # --- transaction volume and fees ---
        volume = demand[t] * state.velocity * volume_noise[t]
        volume_history[t] = volume
        to_reserve, to_geno = fee_flows(volume, mech)
        state.reserve_value += to_reserve

        # --- oracle read and mirror response ---
        observed = observe_m_fiat(
            m_fiat_true, t, sc.oracle_lag, sc.oracle_noise, rng
        )
        d_supply = cic_supply_delta(state, observed, prev_observed, mech)
        state.cic_supply = max(state.cic_supply + d_supply, 0.0)
        prev_observed = observed

        # --- velocity governor ---
        state.velocity = measure_velocity(
            volume_history, state.cic_supply, t, mech.velocity_window
        )
        state.geno_supply = max(
            state.geno_supply + geno_delta(state, mech, to_geno), 0.0
        )

        # --- redemption run ---
        if sc.redemption_run_step is not None and t == sc.redemption_run_step:
            requested = state.claims_outstanding * sc.redemption_run_fraction
            state.redemption_queue.append(
                (t + sc.redemption_settlement_lag, requested)
            )
            state.pending_redemptions += requested

        claims_retired, paid = settle_redemptions(state, res, t)
        state.claims_outstanding = max(state.claims_outstanding - claims_retired, 0.0)
        state.cic_supply = max(state.cic_supply - claims_retired, 0.0)
        state.reserve_value = max(state.reserve_value - paid, 0.0)
        state.pending_redemptions = max(state.pending_redemptions - claims_retired, 0.0)

        # --- price ---
        state.price = price_update(state, res, demand[t], d_supply)

        rows.append(
            {
                "step": t,
                "m_fiat_true": state.m_fiat,
                "m_fiat_observed": observed,
                "cic_supply": state.cic_supply,
                "geno_supply": state.geno_supply,
                "reserve_value": state.reserve_value,
                "claims_outstanding": state.claims_outstanding,
                "backing_ratio": backing_ratio(state, res),
                "velocity": state.velocity,
                "volume": volume,
                "price": state.price,
                "pending_redemptions": state.pending_redemptions,
                "floor_breached": state.floor_breached,
            }
        )

    return pd.DataFrame(rows)
